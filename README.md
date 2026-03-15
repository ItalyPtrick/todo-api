# Todo API

基于 FastAPI + SQLAlchemy + SQLite 的待办事项 REST API。

## 技术栈

- FastAPI 0.135
- SQLAlchemy 2.0
- SQLite
- Pydantic v2
- Uvicorn

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

```bash
# 新建 .env 文件
DATABASE_URL=sqlite:///./todo.db
```

4. 启动服务

```bash
uvicorn main:app --reload
```

5. 访问接口文档：http://127.0.0.1:8000/docs

---

## 数据库字段

| 字段         | 类型     | 说明                     |
| ------------ | -------- | ------------------------ |
| id           | int      | 主键，自动生成           |
| title        | str      | 标题，最长 100 字        |
| completed    | bool     | 是否完成，默认 false     |
| priority     | int      | 优先级，只能是 1 / 2 / 3 |
| due_date     | datetime | 截止时间，可为空         |
| created_at   | datetime | 创建时间，自动填入       |
| updated_at   | datetime | 修改时间，每次更新自动刷新 |

---

## 接口列表

| 方法   | 路径             | 说明         |
| ------ | ---------------- | ------------ |
| POST   | /todos/          | 创建任务     |
| GET    | /todos/          | 获取任务列表 |
| GET    | /todos/stats     | 获取统计数据 |
| GET    | /todos/{id}      | 获取单条任务 |
| PUT    | /todos/{id}      | 更新任务     |
| DELETE | /todos/{id}      | 删除任务     |

---

## GET /todos/ 查询参数

| 参数      | 类型   | 说明                                          |
| --------- | ------ | --------------------------------------------- |
| skip      | int    | 分页偏移，默认 0                              |
| limit     | int    | 每页数量，默认 10                             |
| completed | bool   | 按完成状态筛选                                |
| priority  | int    | 按优先级筛选（1 / 2 / 3）                     |
| search    | str    | 标题模糊搜索                                  |
| sort_by   | str    | 排序字段：priority / created_at / due_date    |
| order     | str    | 排序方向：asc（默认）/ desc                   |

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

| 字段     | 规则                          |
| -------- | ----------------------------- |
| title    | 不能为空白字符，最长 100 字   |
| priority | 只能是 1、2、3                |

校验失败返回 `422 Unprocessable Entity`，响应体会说明哪个字段出了什么问题。

---

## 项目结构

```
todo_api/
├── routers/
│   ├── __init__.py
│   └── todos.py      # 所有路由和业务逻辑
├── .env              # 环境变量（不提交 Git）
├── .gitignore
├── database.py       # 数据库连接
├── main.py           # 应用入口
├── models.py         # 数据库表结构
├── schemas.py        # 请求/响应数据格式
├── requirements.txt
└── README.md
```

各文件职责：

- `main.py` — 应用入口，注册路由，启动服务
- `database.py` — 创建数据库连接，提供 Session
- `models.py` — 定义数据库表结构（SQLAlchemy ORM）
- `schemas.py` — 定义 API 输入输出格式，校验数据（Pydantic）
- `routers/todos.py` — 处理所有 Todo 相关的增删改查逻辑
