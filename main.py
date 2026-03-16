from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import todos

# 创建应用
app = FastAPI(title="Todo API")
"""创建整个应用的实例.
title 只是给 /docs 页面的标题用，设置文档页面左上角看到的 "Todo API" 。

"""

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
"""
中间件 是什么：每个请求到达路由函数之前，都会先经过中间件处理。可以理解成请求的"过滤层"。
请求进来 → 中间件处理 → 路由函数 → 中间件处理 → 返回响应

CORS 是什么问题：浏览器有一个安全限制，叫同源策略。默认情况下：

前端运行在 http://localhost:3000
后端运行在 http://localhost:8000
← 端口不同，浏览器认为是"跨域"，直接拦截请求
加了 CORSMiddleware 之后，后端在响应里加上允许跨域的 HTTP 头，浏览器看到就放行了。
三个 ["*"] 的意思：

allow_origins=["*"] — 允许任何域名的前端访问
allow_methods=["*"] — 允许 GET/POST/PUT/DELETE 所有方法
allow_headers=["*"] — 允许所有请求头

"""

# 挂载路由
app.include_router(todos.router, prefix="/todos", tags=["todos"])
"""
这行做了两件事：
1.
prefix="/todos"  — 把 `todos.py` 里所有路由都加上 `/todos` 前缀

2.
router.post("/")        →   实际路径变成 /todos/
router.get("/{id}")     →   实际路径变成 /todos/{id}
router.delete("/{id}")  →   实际路径变成 /todos/{id}

"""


# 根路径
@app.get("/")
def root():
    return {"message": "Todo API is running"}


"""
这个接口唯一的作用是确认服务在跑。
访问 `http://127.0.0.1:8000/` 能看到这个响应，说明服务正常。

注意这里用的是 `@app.get` 而不是 `@router.get`，
因为这条路由直接挂在 `app` 上，不属于任何业务模块。
"""

"""
 main.py 的启动顺序:

服务启动
    ↓
Base.metadata.create_all()  建表（如果不存在）
    ↓
app = FastAPI()  创建应用
    ↓
add_middleware()  注册中间件
    ↓
include_router()  注册路由
    ↓
开始监听请求

"""
