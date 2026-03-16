import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import Base
from routers.todos import get_db

# 1.创建内存数据库引擎
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# 2.创建测试用的 Session 工厂
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 3.核心 fixture：测试前创建数据库表，测试后关闭连接
@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)  # 创建数据库表
    db = TestingSessionLocal()  # 创建数据库会话
    try:
        yield db  # 把会话传给测试函数，测试函数用完后继续往下走
    finally:
        db.close()  # 关闭数据库连接
        Base.metadata.drop_all(
            bind=engine
        )  # 删除数据库表 (注意是放在finally这里，确保不管测试成功失败都能执行)


# 4.核心 fixture：提供测试用的HTTP客户端，每个请求自动使用上面的测试数据库
@pytest.fixture()
def client(db):
    # 覆盖掉 app 里真实的 get_db 函数，注入测试数据库
    def override_get_db():
        try:
            yield db
        finally:
            pass

    # 让 FastAPI 知道：每次路由里用到 Depends(get_db) 的时候，改成调用 override_get_db
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()  # 测试结束后清除覆盖，恢复原状
