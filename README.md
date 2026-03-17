# Todo API

基于 FastAPI + SQLAlchemy + SQLite 的待办事项 REST API，支持 JWT 用户认证与数据隔离。

## 技术栈

- FastAPI 0.135
- SQLAlchemy 2.0
- SQLite
- Pydantic v2
- Uvicorn
- Alembic 1.18
- python-jose（JWT）
- passlib + bcrypt（密码哈希）

## 本地运行

1. 克隆项目

```bash
git clone https://github.com/ItalyPtrick/todo-api.git
cd todo-api
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 配置环境变量

新建 `.env` 文件：

```
DATABASE_URL=sqlite:///./todo.db
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

`SECRET_KEY` 建议用以下命令生成：

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

4. 初始化数据库

```bash
alembic upgrade head
```

5. 启动服务

```bash
uvicorn main:app --reload
```

6. 访问接口文档：http://127.0.0.1:8000/docs

---

## 认证流程

所有 `/todos` 接口需要登录后才能访问。

```
POST /auth/register   注册账号
POST /auth/login      登录，获取 access_token
```

登录成功后，在请求 Header 中携带 Token：

```
Authorization: Bearer <access_token>
```

Token 有效期为 30 分钟，过期后需重新登录。

---

## 数据隔离

每条 Todo 归属于创建它的用户，用户只能查看和操作自己的数据。

---

## 数据库迁移

项目使用 Alembic 管理数据库结构变更。

修改 `models.py` 后，按以下步骤生成并执行迁移：

```bash
alembic revision --autogenerate -m "描述这次改了什么"
alembic upgrade head
```

回滚上一个版本：

```bash
alembic downgrade -1
```

---

## 数据库字段

### todos 表

| 字段       | 类型     | 说明                       |
| ---------- | -------- | -------------------------- |
| id         | int      | 主键，自动生成             |
| title      | str      | 标题，最长 100 字          |
| completed  | bool     | 是否完成，默认 false       |
| priority   | int      | 优先级，只能是 1 / 2 / 3   |
| due_date   | datetime | 截止时间，可为空           |
| created_at | datetime | 创建时间，自动填入         |
| updated_at | datetime | 修改时间，每次更新自动刷新 |
| owner_id   | int      | 外键，关联 users.id        |

### users 表

| 字段            | 类型     | 说明                   |
| --------------- | -------- | ---------------------- |
| id              | int      | 主键，自动生成         |
| username        | str      | 用户名，唯一           |
| hashed_password | str      | bcrypt 哈希后的密码    |
| created_at      | datetime | 注册时间，自动填入     |

---

## 接口列表

### 认证

| 方法 | 路径             | 说明             | 是否需要 Token |
| ---- | ---------------- | ---------------- | -------------- |
| POST | /auth/register   | 注册             | 否             |
| POST | /auth/login      | 登录，获取 Token | 否             |

### Todo

| 方法   | 路径         | 说明         | 是否需要 Token |
| ------ | ------------ | ------------ | -------------- |
| POST   | /todos/      | 创建任务     | ✅             |
| GET    | /todos/      | 获取任务列表 | ✅             |
| GET    | /todos/stats | 获取统计数据 | ✅             |
| GET    | /todos/{id}  | 获取单条任务 | ✅             |
| PUT    | /todos/{id}  | 更新任务     | ✅             |
| DELETE | /todos/{id}  | 删除任务     | ✅             |

---

## GET /todos/ 查询参数

| 参数      | 类型 | 说明                                       |
| --------- | ---- | ------------------------------------------ |
| skip      | int  | 分页偏移，默认 0                           |
| limit     | int  | 每页数量，默认 10                          |
| completed | bool | 按完成状态筛选                             |
| priority  | int  | 按优先级筛选（1 / 2 / 3）                  |
| search    | str  | 标题模糊搜索                               |
| sort_by   | str  | 排序字段：priority / created_at / due_date |
| order     | str  | 排序方向：asc（默认）/ desc                |

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

## 输入校验规则

| 字段     | 规则                        |
| -------- | --------------------------- |
| title    | 不能为空白字符，最长 100 字 |
| priority | 只能是 1、2、3              |
| username | 长度 3 - 50 字符            |
| password | 长度 6 - 72 字符            |

校验失败返回 `422 Unprocessable Entity`，响应体会说明哪个字段出了什么问题。

---

## 项目结构

```
todo_api/
├── alembic/
│   ├── versions/     # 迁移版本文件
│   ├── env.py        # Alembic 核心配置
│   └── script.py.mako
├── routers/
│   ├── __init__.py
│   ├── todos.py      # Todo 路由
│   └── auth.py       # 认证路由（注册、登录）
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_todos.py
├── .env              # 环境变量（不提交 Git）
├── .gitignore
├── alembic.ini       # Alembic 配置
├── auth_utils.py     # 密码哈希、JWT 工具函数
├── database.py       # 数据库连接
├── main.py           # 应用入口
├── models.py         # 数据库表结构
├── schemas.py        # 请求/响应数据格式
├── requirements.txt
└── README.md
```

各文件职责：

- `main.py` — 应用入口，注册路由，启动服务
- `database.py` — 创建数据库连接，提供 Session 和 get_db 依赖
- `models.py` — 定义数据库表结构（SQLAlchemy ORM）
- `schemas.py` — 定义 API 输入输出格式，校验数据（Pydantic）
- `auth_utils.py` — 密码哈希（bcrypt）、JWT 生成与验证、get_current_user 依赖
- `routers/todos.py` — Todo 增删改查路由，所有接口需要认证
- `routers/auth.py` — 注册、登录路由
- `alembic/` — 数据库迁移配置和版本历史
