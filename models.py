from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey

# 从 SQLAlchemy 导入字段类型
from database import Base
from datetime import datetime, timezone


class Todo(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    completed = Column(Boolean, default=False)
    priority = Column(Integer, default=2)
    due_date = Column(DateTime, nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )  # 每次插入新记录时自动调用这个函数填入当前时间，不需要手动传值。
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    owner_id = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )  # 外键，关联到 users 表的 id 字段，表示这个待办事项属于哪个用户。nullable=False 表示这个字段不能为空，每个待办事项必须有一个所属用户。


"""
翻译成 SQL 就是：
CREATE TABLE todos (
    id      INTEGER PRIMARY KEY,
    title   VARCHAR NOT NULL,
    completed BOOLEAN DEFAULT false
);

models.py — 描述数据库表长什么样
schemas.py — 描述 API 的输入输出长什么样
"""


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
