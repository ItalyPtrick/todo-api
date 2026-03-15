from pydantic import BaseModel
from datetime import datetime

class TodoCreate(BaseModel):
    title: str
    completed: bool = False
    priority: int = 2
    due_date: datetime | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "学 FastAPI 路由",
                "completed": False,
                "priority": 2,
                "due_date": "2025-04-01T00:00:00"
            }
        }
    }

class TodoUpdate(BaseModel):
    title: str | None = None
    completed: bool | None = None
    priority: int | None = None
    due_date: datetime | None = None

class TodoResponse(BaseModel):
    id: int
    title: str
    completed: bool
    priority: int
    due_date: datetime | None

    model_config = {"from_attributes": True}