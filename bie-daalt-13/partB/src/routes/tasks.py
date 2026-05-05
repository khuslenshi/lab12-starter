from fastapi import APIRouter, Query
from typing import Optional, List
from models import TaskCreate, TaskUpdate, TaskResponse
import services

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate):
    """Шинэ task үүсгэх"""
    return await services.create_task(task)


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    status: Optional[str] = Query(None, description="todo | in_progress | done"),
    priority: Optional[str] = Query(None, description="low | medium | high"),
    label: Optional[str] = Query(None, description="Label-аар шүүх"),
    search: Optional[str] = Query(None, description="Гарчиг/тайлбараар хайх"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Task жагсаалт — filter болон search-тэй"""
    return await services.get_all_tasks(status, priority, label, search, skip, limit)


@router.get("/labels", response_model=List[str])
async def list_labels():
    """Бүх label жагсаалт"""
    return await services.get_labels()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """ID-аар task авах"""
    return await services.get_task(task_id)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, task: TaskUpdate):
    """Task засах (partial update)"""
    return await services.update_task(task_id, task)


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    """Task устгах"""
    return await services.delete_task(task_id)
