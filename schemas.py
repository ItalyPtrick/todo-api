from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime


class TodoCreate(BaseModel):
    title: str = Field(max_length=100)
    completed: bool = False
    priority: int = Field(
        default=2, ge=1, le=3
    )  # ge = greater or equal，le = less or equal，priority 必须 ≥1 且 ≤3。
    due_date: datetime | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v):
        if not v.strip():
            raise ValueError("标题不能是空白字符")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "学 FastAPI 路由",
                "completed": False,
                "priority": 2,
                "due_date": "2025-04-01T00:00:00",
            }
        }
    }


class TodoUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=100)
    completed: bool | None = None
    priority: int | None = Field(default=None, ge=1, le=3)
    due_date: datetime | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v):
        if v is not None and not v.strip():
            raise ValueError("标题不能是空白字符")
        return v


class TodoResponse(BaseModel):
    id: int
    title: str
    completed: bool
    priority: int
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}

    # ORM 对象不是字典，Pydantic 默认只认字典，加了 from_attributes=True 才能直接读对象属性完成转换。
    # ORM 对象是什么?
    # ORM 是 **Object Relational Mapping**，对象关系映射


class TodoStats(BaseModel):
    total: int
    completed: int
    uncompleted: int


"""
SQLAlchemy 查出来的 Todo 对象长这样：
python<Todo id=1 title="学FastAPI" completed=False>  # 这是一个 ORM 对象

Pydantic 的 TodoResponse 需要的是：
{"id": 1, "title": "学FastAPI", "completed": False}  # 这是一个字典
'''

'''
`from_attributes=True` (默认False)告诉 Pydantic：
你可以直接读对象的属性来转换，不需要先变成字典。
没有这行，FastAPI 返回数据时会报错。

加了 from_attributes=True 之后，Pydantic 会改变读取方式：
1. from_attributes=False 时，Pydantic 这样读数据：
data["id"]       # 字典取值方式

2. from_attributes=True 时，Pydantic 这样读数据：
data.id          # 对象属性取值方式
"""


"""
schemas.py` 总结：

用户发来请求
    ↓
TodoCreate / TodoUpdate 校验数据格式
    ↓
路由函数处理，操作数据库
    ↓
TodoResponse 把 ORM 对象转成 JSON 返回给用户
"""

# ---- User Schemas ----


# 规定注册接口接收什么
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=72)


# 规定注册接口返回什么（不包含密码相关字段）
class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime

    """from_attributes=True 的作用是告诉 Pydantic：
你可以直接读对象的属性来转换，不需要先变成字典。"""
    model_config = ConfigDict(from_attributes=True)


# 规定登录接口返回什么
class Token(BaseModel):
    access_token: str  # JWT 字符串
    token_type: str
