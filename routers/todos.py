from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Todo
from schemas import TodoCreate, TodoUpdate, TodoResponse

router = APIRouter()
# 创建了一个路由集合，后面所有的 @router.get()、@router.post() 都是往这个集合里登记规则。


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


# 创建任务
@router.post("/", response_model=TodoResponse, status_code=201)
async def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    db_todo = Todo(
        title=todo.title,
        completed=todo.completed,
        priority=todo.priority,
        due_date=todo.due_date,
    )
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo


"""
db.refresh(db_todo) 这行很关键，
创建对象时只设置了 title，id 是数据库自动生成的。
commit() 之后数据库里有了 id，但内存里的 db_todo 对象还不知道自己的 id 是几。
refresh() 就是让对象去数据库重新拿一遍自己的数据，这样返回给用户时 id 才有值。
"""


# 查询所有任务
@router.get("/", response_model=list[TodoResponse])
async def get_todos(
    skip: int = 0,
    limit: int = 10,
    completed: bool | None = None,
    search: str | None = None,
    priority: int | None = None,
    sort_by: str | None = None,
    order: str = "asc",
    db: Session = Depends(get_db),
):
    query = db.query(Todo)
    if completed is not None:
        query = query.filter(Todo.completed == completed)

    if search is not None:
        query = query.filter(
            Todo.title.contains(search)
        )  # contains("FastAPI") 对应的 SQL 是 WHERE title LIKE '%FastAPI%'，匹配标题里任何位置包含这个词的记录。

    if priority is not None:
        query = query.filter(Todo.priority == priority)

    # 这是一个字典，把前端可能传的排序字段名 映射 到真实的数据库字段（SQLAlchemy的列对象）
    SORT_FIELDS = {
        "priority": Todo.priority,
        "created_at": Todo.created_at,
        "due_date": Todo.due_date,
    }

    # 判断用户是否传了我们支持的排序字段
    if sort_by in SORT_FIELDS:
        # 从字典里取出对应的 SQLAlchemy Column 对象
        column = SORT_FIELDS[sort_by]

        # 逻辑是：主排序按用户指定的字段， 次级排序固定 是 `created_at` 降序**（越新创建的越靠前）。
        # `order` 参数只控制主排序方向，次级排序始终不变。

        if order == "desc":
            query = query.order_by(column.desc(), Todo.created_at.desc())
        else:
            query = query.order_by(column.asc(), Todo.created_at.asc())

    return query.offset(skip).limit(limit).all()


# db.query(Todo).all() 翻译成 SQL 就是：
# SELECT * FROM todos;
# query决定了查哪个表


# 查询单条任务
@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    # filter(Todo.id == todo_id).first() 翻译成 SQL：
    # SELECT * FROM todos WHERE id = 1 LIMIT 1;

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


# 更新任务
@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(todo_id: int, todo: TodoUpdate, db: Session = Depends(get_db)):
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not db_todo:
        raise HTTPException(
            status_code=404, detail="Todo not found"
        )  # 先查有没有，没有返回 404
    if todo.title is not None:
        db_todo.title = todo.title
    if todo.completed is not None:
        db_todo.completed = todo.completed
    if todo.priority is not None:
        db_todo.priority = todo.priority
    if todo.due_date is not None:
        db_todo.due_date = todo.due_date

    db.commit()  # 这时SQLAlchemy会追踪变化，并翻译成：
    # UPDATE todos SET completed = true WHERE id = 1;
    db.refresh(db_todo)
    return db_todo


# 删除任务
@router.delete(
    "/{todo_id}", status_code=204
)  # status_code=204 表示成功但没有返回内容，所以这个函数没有 return。
# 204 是删除操作的标准状态码。
async def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    db.delete(db_todo)  # DELETE FROM todos WHERE id = 1;
    db.commit()


"""
## 整个请求的完整流程

用一个具体例子串起来，`GET /todos/1`：

浏览器发送请求 GET /todos/1
        ↓
FastAPI 匹配到 @router.get("/{todo_id}")
        ↓
执行 Depends(get_db)，创建数据库连接
        ↓
执行 get_todo(todo_id=1, db=<连接>)
        ↓
db.query(Todo).filter(Todo.id == 1).first()
        ↓
SQLAlchemy 翻译成 SELECT * FROM todos WHERE id=1
        ↓
从 todo.db 文件里找到这行记录
        ↓
返回 ORM 对象，TodoResponse 转成 JSON
        ↓
{"id":1, "title":"学FastAPI", "completed":false}
        ↓
浏览器收到响应
"""
