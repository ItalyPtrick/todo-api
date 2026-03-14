from pydantic import BaseModel


class TodoCreate(BaseModel):  # 创建任务时接收的请求体格式。
    title: str


class TodoUpdate(BaseModel):  # 更新任务时接收的请求体格式。
    title: str | None = None
    completed: bool | None = None


class TodoResponse(BaseModel):  # 返回给用户的响应格式。
    id: int
    title: str
    completed: bool

    model_config = {"from_attributes": True}
    #ORM 对象不是字典，Pydantic 默认只认字典，加了 from_attributes=True 才能直接读对象属性完成转换。
    # ORM 对象是什么?
    # ORM 是 **Object Relational Mapping**，对象关系映射


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
