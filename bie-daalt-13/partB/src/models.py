from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Status(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    priority: Priority = Priority.medium
    status: Status = Status.todo
    due_date: Optional[datetime] = None
    labels: List[str] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Шинэ даалгавар",
                "description": "Энэ даалгаврын тайлбар",
                "priority": "high",
                "status": "todo",
                "due_date": "2025-12-31T00:00:00",
                "labels": ["work", "urgent"]
            }
        }
    }


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    priority: Optional[Priority] = None
    status: Optional[Status] = None
    due_date: Optional[datetime] = None
    labels: Optional[List[str]] = None


class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    priority: Priority
    status: Status
    due_date: Optional[datetime]
    labels: List[str]
    created_at: datetime
    updated_at: datetime
