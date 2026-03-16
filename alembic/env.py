# 导入日志配置工具（Alembic 默认会用）
from logging.config import fileConfig

# SQLAlchemy 引擎创建函数 + 连接池
from sqlalchemy import engine_from_config, pool

# Alembic 的上下文对象（非常核心）
from alembic import context

import sys
import os

# 把项目根目录加到 sys.path，这样就能 import database 和 models
# 让 Python 能够找到这些模块(必须插入到搜索路径最前面)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载 .env 文件（把环境变量读进来）
from dotenv import load_dotenv

load_dotenv()  # 读取 .env 里的 DATABASE_URL

# 导入 SQLAlchemy Base（所有模型的元数据都在这里）
from database import Base

# 必须 import models！不然 Alembic 看不到任何表定义
import models

# 获取 Alembic 当前运行的配置（来自 alembic.ini）
config = context.config

# 从 .env 读取真实数据库 URL，强制覆盖 alembic.ini 里的配置
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))

# 如果有 alembic.ini 里的日志配置文件，就加载它
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 告诉 Alembic：用这个 metadata 来对比数据库结构
# （Base.metadata 包含所有 Model 的表定义）
target_metadata = Base.metadata


# ==============================
# 离线模式（生成 SQL 语句，不真正执行）
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,  # 把参数直接写进 SQL（方便看）
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()  # 生成迁移 SQL 到控制台或文件


# ==============================
# 在线模式（真正连接数据库执行迁移）
def run_migrations_online() -> None:
    # 从配置创建数据库引擎（用 NullPool 表示不使用连接池）
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # 迁移时通常不用连接池
    )

    # 建立连接
    with connectable.connect() as connection:
        # 配置上下文
        context.configure(connection=connection, target_metadata=target_metadata)
        # 开始事务并执行迁移
        with context.begin_transaction():
            context.run_migrations()


# 根据运行模式选择执行哪个函数
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
