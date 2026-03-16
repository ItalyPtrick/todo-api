"""
导入四个东西：
create_engine：创建数据库连接引擎
declarative_base：所有数据库表的"基类"，后面 models.py 会用
sessionmaker：生产数据库 Session 的工厂
load_dotenv + os：用来读取 .env 文件里的配置
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()  # 把 `.env` 文件里的内容加载到环境变量里

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)  # os.getenv("DATABASE_URL") 读取其中的 DATABASE_URL

"""
engine 是数据库的"连接器"，负责真正跟数据库文件通信。
check_same_thread=False 是 SQLite 专属的配置。SQLite 默认只允许创建它的那个线程使用它，但 FastAPI 是异步多线程的，所以要关掉这个限制。换成 PostgreSQL 这行不需要。
"""
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

"""
sessionmaker 是一个工厂，SessionLocal 是它生产出来的"Session 模板"。
每次调用 SessionLocal() 就会创建一个新的数据库 Session。Session 是什么？可以理解成一次数据库会话——你在里面做的所有操作（增删改查），最后统一 commit() 才真正写入数据库。

autocommit=False：不自动提交，需要手动 db.commit()，这样出错了可以回滚
autoflush=False：不自动把内存里的变化同步到数据库，由你控制时机
"""
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


Base = (
    declarative_base()
)  # Base 是所有数据库表类的父类。后面 models.py 里写 class Todo(Base)，SQLAlchemy 才知道 `Todo` 是一张数据库表，不是普通的 Python 类。

"""
`database.py` 总结：

.env 文件
  ↓ load_dotenv() 读取
DATABASE_URL
  ↓ create_engine() 连接
engine（连接器）
  ↓ sessionmaker() 包装
SessionLocal（Session 工厂）
  ↓ 每次请求调用一次
db（一次数据库会话）
"""


# 依赖注入：每个请求自动获取数据库连接，用完自动关闭
def get_db():
    db = SessionLocal()
    try:
        yield db  # 普通函数用 `return`，执行完就结束了。用 `yield` 的函数叫生成器，它可以暂停
    finally:
        db.close()


"""
Depends(get_db) 的意思是：每次这个路由被调用时，自动先执行 get_db，把结果作为 db 参数传进来。

你不需要在每个路由里手动写：
db = SessionLocal()
# ... 用完
db.close()
"""
