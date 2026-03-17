# Todo API

FastAPI + SQLAlchemy 实现的待办事项 REST API，支持 JWT 用户认证与数据隔离。

**线上地址**：https://todo-api-s0hq.onrender.com  
**接口文档**：https://todo-api-s0hq.onrender.com/docs

> 免费托管，首次访问冷启动约需 30–50 秒。

---

## 技术栈

- **FastAPI** 0.135 — Web 框架
- **SQLAlchemy** 2.0 — ORM
- **PostgreSQL**（生产）/ SQLite（本地开发）
- **Pydantic v2** — 数据校验
- **Alembic** 1.18 — 数据库迁移
- **python-jose** — JWT
- **passlib + bcrypt** — 密码哈希
- **Uvicorn** — ASGI 服务器

---

## 本地运行

**前置条件**：Python 3.10+，建议使用虚拟环境。
```bash
git clone https://github.com/ItalyPtrick/todo-api.git
cd todo-api
pip install -r requirements.txt
```

新建 `.env` 文件：
```
DATABASE_URL=sqlite:///./todo.db
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

`SECRET_KEY` 生成方式：
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

初始化数据库并启动：
```bash
alembic upgrade head
uvicorn main:app --reload
```

访问 http://127.0.0.1:8000/docs

---

## 部署

生产环境使用 **Render**（Web Service）+ **Supabase**（PostgreSQL）。

启动命令：
```bash
alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT
```

需要在平台配置以下环境变量：
```
DATABASE_URL=        # Supabase Session Pooler URL
SECRET_KEY=          # 与本地相同或重新生成
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## 认证流程

所有 `/todos` 接口需要携带 Token。
```
POST /auth/register   注册
POST /auth/login      登录，返回 access_token
```

登录后在请求 Header 中添加：
```
Authorization: Bearer <access_token>
```

Token 有效期 30 分钟。

---

## 数据隔离

每条 Todo 通过 `owner_id` 外键绑定到创建它的用户，接口层面自动过滤，用户只能看到自己的数据。

---

## 接口列表

### 认证

| 方法 | 路径 | 说明 | 需要 Token |
| --- | --- | --- | --- |
| POST | /auth/register | 注册 | 否 |
| POST | /auth/login | 登录 | 否 |

### Todo

| 方法 | 路径 | 说明 | 需要 Token |
| --- | --- | --- | --- |
| POST | /todos/ | 创建 | ✅ |
| GET | /todos/ | 列表（支持筛选排序） | ✅ |
| GET | /todos/stats | 统计 | ✅ |
| GET | /todos/{id} | 详情 | ✅ |
| PUT | /todos/{id} | 更新 | ✅ |
| DELETE | /todos/{id} | 删除 | ✅ |

---

## GET /todos/ 查询参数

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| skip | int | 分页偏移，默认 0 |
| limit | int | 每页数量，默认 10 |
| completed | bool | 按完成状态筛选 |
| priority | int | 按优先级筛选（1 / 2 / 3） |
| search | str | 标题模糊搜索 |
| sort_by | str | 排序字段：priority / created_at / due_date |
| order | str | asc（默认）/ desc |

示例：
```
GET /todos/?sort_by=priority&order=asc
GET /todos/?completed=false&sort_by=due_date&order=asc
GET /todos/?search=FastAPI&priority=1
```

---

## GET /todos/stats 响应示例
```json
{
  "total": 10,
  "completed": 4,
  "uncompleted": 6
}
```

---

## 输入校验

| 字段 | 规则 |
| --- | --- |
| title | 不能为空白字符，最长 100 字 |
| priority | 只能是 1、2、3 |
| username | 3–50 字符 |
| password | 6–72 字符 |

校验失败返回 `422`，响应体包含具体字段和原因。

---

## 数据库字段

### todos

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 主键 |
| title | str | 标题，最长 100 字 |
| completed | bool | 默认 false |
| priority | int | 1 / 2 / 3 |
| due_date | datetime | 截止时间，可为空 |
| created_at | datetime | 创建时间，自动填入 |
| updated_at | datetime | 修改时间，自动刷新 |
| owner_id | int | 外键，关联 users.id |

### users

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 主键 |
| username | str | 唯一 |
| hashed_password | str | bcrypt 哈希 |
| created_at | datetime | 注册时间，自动填入 |

---

## 数据库迁移
```bash
# 生成新迁移
alembic revision --autogenerate -m "描述变更内容"

# 执行迁移
alembic upgrade head

# 回滚一步
alembic downgrade -1
```

---

## 项目结构
```
todo_api/
├── alembic/
│   ├── versions/       # 迁移版本文件
│   ├── env.py
│   └── script.py.mako
├── routers/
│   ├── auth.py         # 注册、登录
│   └── todos.py        # Todo CRUD
├── tests/
│   ├── conftest.py
│   └── test_todos.py
├── auth_utils.py       # JWT 与密码工具函数
├── database.py         # 数据库连接与 Session
├── main.py             # 应用入口
├── models.py           # ORM 表结构
├── schemas.py          # Pydantic 请求/响应模型
└── requirements.txt
```