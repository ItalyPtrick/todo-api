from sqlalchemy import Column, Integer, String, Boolean #从 SQLAlchemy 导入字段类型
from database import Base #从 database.py 导入刚才说的那个 Base

class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    completed = Column(Boolean, default=False)


'''
翻译成 SQL 就是：
CREATE TABLE todos (
    id      INTEGER PRIMARY KEY,
    title   VARCHAR NOT NULL,
    completed BOOLEAN DEFAULT false
);

models.py — 描述数据库表长什么样
schemas.py — 描述 API 的输入输出长什么样
'''