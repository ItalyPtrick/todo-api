---
title: Todo API 部署心得与踩坑记录
tags:
  - 后端开发
  - FastAPI
  - PostgreSQL
  - 部署
  - DevOps
  - 学习笔记
created: 2025-06
updated: 2025-06
status: 完成
project: todo-api
stack:
  - FastAPI
  - SQLAlchemy
  - PostgreSQL
  - Alembic
  - JWT
  - GitHub Actions
  - ClawCloud
---

# 🚀 Todo API 部署心得与踩坑记录

> [!abstract] 文档概览
> 本文记录 Todo API 从本地开发到云端部署的完整踩坑过程，涵盖 Alembic 迁移、数据库选型、容器配置、CI/CD 流程等核心问题，适合作为 FastAPI 项目部署的参考手册。

---

## 📦 技术栈一览

| 层级 | 技术 | 说明 |
|------|------|------|
| **Web 框架** | FastAPI | 异步 Python 后端 |
| **ORM** | SQLAlchemy | 数据库抽象层 |
| **数据库** | PostgreSQL | 生产级关系型数据库 |
| **迁移工具** | Alembic | 数据库版本管理 |
| **认证** | JWT | Token 鉴权 |
| **容器平台** | ClawCloud | 后端容器托管 |
| **CI/CD** | GitHub Actions | 自动构建 + 推送镜像 |
| **镜像仓库** | ghcr.io | GitHub Container Registry |

---

## 🗺️ 最终决策路径

```
初始方案
  └─ Render（后端）+ Supabase（PostgreSQL）
        │
        ├─ ❌ 发现 Supabase 免费 PostgreSQL 仅 30 天
        │
        └─ 改用 ClawCloud 全家桶
              ├─ ClawCloud 容器（后端）
              └─ ClawCloud PostgreSQL（数据库）✅
```

> [!tip] 选型结论
> ClawCloud 全家桶方案更稳定，数据库与容器在同一平台，网络延迟低，且免费额度相对充裕。

---

## 🪲 踩坑详解

### 坑 1：Alembic 迁移文件顺序写错

> [!bug] 问题描述
> `upgrade()` 函数中先执行了 `UPDATE`（数据回填），但对应的 `ADD COLUMN` 写在其后，导致迁移执行时字段不存在，直接报错。

**错误写法**

```python
def upgrade() -> None:
    # ❌ 字段还没有，就先 UPDATE，必然报错
    op.execute("UPDATE todos SET priority = 'medium' WHERE priority IS NULL")
    op.add_column('todos', sa.Column('priority', sa.String(), nullable=True))
```

**正确写法**

```python
def upgrade() -> None:
    # ✅ 先加列，再回填数据
    op.add_column('todos', sa.Column('priority', sa.String(), nullable=True))
    op.execute("UPDATE todos SET priority = 'medium' WHERE priority IS NULL")
    op.alter_column('todos', 'priority', nullable=False)
```

> [!note] 心得
> Alembic 迁移的操作顺序必须与 SQL 执行逻辑一致：**结构变更 → 数据回填 → 约束收紧**。每次写完迁移文件，先在本地用 `alembic upgrade head` 跑一遍验证，再推到生产环境。

---

### 坑 2：Render 免费 PostgreSQL 有效期误判

> [!warning] 常见误区
> 很多文档（包括部分 Render 官方早期说明）写的是"免费数据库 90 天"，实际上 **2024 年后政策已变更为 30 天**，到期后数据库会被删除。

**影响**

- 依赖 Render 免费 PostgreSQL 的项目需要在 30 天内迁移或升级付费计划
- 数据库被删除后，容器内的应用直接无法连接，报 `connection refused`

> [!tip] 建议
> 部署前务必查阅平台**当前**的免费套餐政策页面，不要依赖二手资料。免费数据库适合学习项目短期验证，生产级项目需要稳定的付费方案或自托管。

---

### 坑 3：Supabase Direct Connection 不支持 IPv4

> [!bug] 问题描述
> 使用 Supabase 提供的 **Direct Connection** URL 时，部分云平台（尤其是 IPv4-only 的容器环境）无法建立连接，因为 Direct Connection 需要 IPv6。

**解决方案**

| 连接方式 | 适用场景 | 是否支持 IPv4 |
|----------|----------|---------------|
| Direct Connection | 本地开发、IPv6 环境 | ❌ |
| **Session Pooler** | 无状态短连接（FastAPI 场景） | ✅ |
| Transaction Pooler | 无状态极短事务 | ✅ |

在 Supabase 控制台 → Project Settings → Database → **Connection Pooling** 中复制 **Session Pooler** URL：

```
postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres
```

> [!note] 心得
> FastAPI + SQLAlchemy 的长连接模式与 Transaction Pooler 不兼容（会丢失连接状态），应使用 **Session Pooler**。

---

### 坑 4：SQLAlchemy 不识别 `postgres://` 前缀

> [!bug] 问题描述
> 部分平台（如早期 Heroku、Render）提供的数据库 URL 使用 `postgres://` 前缀，但 SQLAlchemy 1.4+ 要求使用 `postgresql://`，直接使用会抛出：
> ```
> sqlalchemy.exc.NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:postgres
> ```

**修复方式**

在应用启动时自动替换前缀：

```python
# config.py 或 database.py
import os

DATABASE_URL = os.getenv("DATABASE_URL", "")

# 兼容性修复：替换旧版前缀
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
```

> [!tip] 更优雅的写法（推荐）
> 使用 `pydantic-settings` 的 `@field_validator` 在模型层统一处理：
> ```python
> @field_validator("DATABASE_URL", mode="before")
> @classmethod
> def fix_postgres_url(cls, v: str) -> str:
>     return v.replace("postgres://", "postgresql://", 1) if v.startswith("postgres://") else v
> ```

---

### 坑 5：环境变量未完整配置到平台

> [!bug] 问题描述
> 本地 `.env` 文件中定义了 `ACCESS_TOKEN_EXPIRE_MINUTES=30`，但部署到 Render 时忘记在 Environment Variables 面板中添加该变量，导致：
> ```
> TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'
> ```

**根因分析**

```python
# settings.py
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
#                                                                                 ^
#                               os.getenv 返回 None，int(None) 报 TypeError
```

**修复方式**

1. 为 `os.getenv` 提供默认值：
   ```python
   ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
   ```

2. 更推荐：使用 `pydantic-settings` 的 `BaseSettings`，字段缺失时会给出明确的验证错误：
   ```python
   from pydantic_settings import BaseSettings

   class Settings(BaseSettings):
       ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 有默认值，部署时不填也能运行
       SECRET_KEY: str                         # 无默认值，缺失时立即报错提示
   ```

> [!note] 心得
> 维护一份 `.env.example` 文件并纳入版本控制，每次部署新平台时对照检查，是避免此类问题的最佳实践。

**`.env.example` 示例**

```dotenv
# 必填
DATABASE_URL=postgresql://user:password@host:5432/dbname
SECRET_KEY=your-secret-key-here

# 可选（有默认值）
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256
```

---

### 坑 6：ClawCloud 容器内存不足（64Mi → 256Mi）

> [!bug] 问题描述
> ClawCloud 默认分配 **64Mi** 内存，Python 解释器本身加上 FastAPI + SQLAlchemy 依赖的启动内存远超此限制，容器启动后立即被 OOM Kill，日志显示：
> ```
> Killed
> ```
> 或容器反复重启（CrashLoopBackOff）。

**内存参考基准（FastAPI 项目）**

| 内存配置 | 状态 |
|----------|------|
| 64Mi | ❌ OOM，无法启动 |
| 128Mi | ⚠️ 勉强启动，高并发下不稳定 |
| **256Mi** | ✅ 正常运行（推荐最低配置） |
| 512Mi | ✅ 生产推荐 |

> [!tip] 诊断方法
> 在 ClawCloud 控制台查看容器的 **Metrics** 面板，若内存曲线在启动阶段直接触顶，说明需要提升内存限制。

---

### 坑 7：ghcr.io Package 默认为私有

> [!bug] 问题描述
> 通过 GitHub Actions 推送镜像到 `ghcr.io` 后，ClawCloud 拉取镜像时报 `unauthorized` 或 `manifest unknown`，原因是 ghcr.io 新建 Package 默认权限为 **Private**。

**两种解决方案**

**方案 A：将 Package 改为 Public（推荐学习项目）**

1. 进入 GitHub → Your Profile → Packages
2. 找到对应的 Container Package
3. Package Settings → Change visibility → **Public**

**方案 B：配置认证拉取（推荐生产项目）**

在 ClawCloud 的镜像配置中填入 Registry Credentials：

```
Registry: ghcr.io
Username: <your-github-username>
Password: <github-pat-with-read:packages-scope>
```

> [!warning] 安全提醒
> GitHub PAT 请使用**细粒度 Token（Fine-grained PAT）**，仅授予 `read:packages` 权限，不要使用 Classic Token 的全权 PAT。

---

### 坑 8：GitHub Actions 缺少 packages write 权限

> [!bug] 问题描述
> GitHub Actions workflow 推送镜像到 ghcr.io 时报：
> ```
> Error: denied: installation not allowed to Write organization package
> ```
> 原因是默认的 `GITHUB_TOKEN` 没有 `packages:write` 权限。

**解决方案**

在 workflow 文件中显式声明权限：

```yaml
# .github/workflows/deploy.yml
name: Build and Push Docker Image

on:
  push:
    branches: [main]

permissions:
  contents: read
  packages: write   # ← 必须显式声明

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Log in to ghcr.io
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and Push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:latest
```

> [!note] 心得
> GitHub Actions 遵循**最小权限原则**，所有需要的权限必须在 `permissions` 块中明确声明。养成每次写 workflow 都检查权限块的习惯。

---

## 🔄 CI/CD 流程总结

```
┌─────────────────────────────────────────────────────────┐
│                   开发工作流                              │
│                                                          │
│  本地开发  →  git push main  →  GitHub Actions 触发      │
│                                    │                     │
│                              ┌─────▼──────┐              │
│                              │ 构建 Docker │              │
│                              │   镜像      │              │
│                              └─────┬──────┘              │
│                                    │                     │
│                              ┌─────▼──────┐              │
│                              │  推送到     │              │
│                              │  ghcr.io   │              │
│                              └─────┬──────┘              │
│                                    │                     │
│                              手动操作                     │
│                                    │                     │
│                              ┌─────▼──────┐              │
│                              │ ClawCloud  │              │
│                              │点击 Update │              │
│                              └─────┬──────┘              │
│                                    │                     │
│                              ┌─────▼──────┐              │
│                              │  拉取新镜像 │              │
│                              │  重启容器  │              │
│                              └────────────┘              │
└─────────────────────────────────────────────────────────┘
```

> [!info] 为何选择半自动而非全自动部署
> ClawCloud 目前不提供原生的 Webhook 触发重启 API（截至本文撰写时），因此采用"CI 自动推镜像 + 手动点 Update"的半自动方案。这对学习项目来说完全够用，且避免了自动部署带来的意外风险。

---

## 💡 综合心得与最佳实践

### 部署前检查清单

> [!check] 每次部署前必做
> - [ ] 本地运行 `alembic upgrade head` 验证迁移无误
> - [ ] 对照 `.env.example` 检查平台环境变量是否完整配置
> - [ ] 确认 Docker 镜像在本地可正常构建并启动
> - [ ] 确认容器内存限制 ≥ 256Mi
> - [ ] 确认 ghcr.io Package 可见性或认证配置正确

### 数据库选型建议

| 需求场景 | 推荐方案 | 原因 |
|----------|----------|------|
| 本地开发/测试 | SQLite | 零配置，方便 |
| 学习项目短期演示 | Supabase Session Pooler | 免费但有 30 天限制，了解清楚再用 |
| 稳定的学习/展示项目 | ClawCloud PostgreSQL | 与容器同平台，连接稳定 |
| 生产级项目 | 付费托管 PostgreSQL | 数据安全第一 |

### 关键经验总结

> [!quote] 这次部署最大的收获
> **"平台文档要看当前版本，不要相信过时的教程。"**
> 
> Render 的免费 PostgreSQL 政策、Supabase 的连接方式、ghcr.io 的默认权限——这些都是随时可能变化的平台策略。每次部署新平台，花 10 分钟看官方最新文档，能省去 3 小时的踩坑时间。

1. **迁移文件是最容易出错的地方**：写完后一定在本地干净数据库上跑一遍 `upgrade` + `downgrade` 验证
2. **环境变量是最容易遗漏的地方**：`.env.example` + `pydantic-settings` 是标配
3. **内存是最容易低估的地方**：Python 应用给 256Mi 起步，不要省这点钱
4. **权限是最容易忘记的地方**：GitHub Actions、ghcr.io、平台 IAM，每个环节都要检查

---

## 🔗 相关资源

- [Alembic 官方文档](https://alembic.sqlalchemy.org/en/latest/)
- [SQLAlchemy 连接字符串说明](https://docs.sqlalchemy.org/en/20/core/engines.html)
- [GitHub Actions 权限文档](https://docs.github.com/en/actions/security-guides/automatic-token-authentication#permissions-for-the-github_token)
- [Supabase 连接方式对比](https://supabase.com/docs/guides/database/connecting-to-postgres)

---

*最后更新：2025-06 | 项目：[[todo-api]] | 阶段：[[Month 3 - FastAPI部署]]*
