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

## 接口列表

| 方法   | 路径        | 说明         |
| ------ | ----------- | ------------ |
| POST   | /todos/     | 创建任务     |
| GET    | /todos/     | 获取所有任务 |
| GET    | /todos/{id} | 获取单条任务 |
| PUT    | /todos/{id} | 更新任务     |
| DELETE | /todos/{id} | 删除任务     |
