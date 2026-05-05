from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import HTTPException
from database import get_db
from models import TaskCreate, TaskUpdate, TaskResponse


def _serialize(task: dict) -> TaskResponse:
    return TaskResponse(
        id=str(task["_id"]),
        title=task["title"],
        description=task.get("description"),
        priority=task["priority"],
        status=task["status"],
        due_date=task.get("due_date"),
        labels=task.get("labels", []),
        created_at=task["created_at"],
        updated_at=task["updated_at"],
    )


def _valid_id(task_id: str) -> ObjectId:
    try:
        return ObjectId(task_id)
    except (InvalidId, Exception):
        raise HTTPException(status_code=400, detail="Invalid task ID format")


async def create_task(data: TaskCreate) -> TaskResponse:
    db = get_db()
    now = datetime.now(timezone.utc)
    doc = {
        **data.model_dump(),
        "created_at": now,
        "updated_at": now,
    }
    result = await db.tasks.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize(doc)


async def get_all_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    label: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[TaskResponse]:
    db = get_db()
    query = {}

    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    if label:
        query["labels"] = label
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    cursor = db.tasks.find(query).skip(skip).limit(limit).sort("created_at", -1)
    tasks = await cursor.to_list(length=limit)
    return [_serialize(t) for t in tasks]


async def get_task(task_id: str) -> TaskResponse:
    db = get_db()
    oid = _valid_id(task_id)
    task = await db.tasks.find_one({"_id": oid})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _serialize(task)


async def update_task(task_id: str, data: TaskUpdate) -> TaskResponse:
    db = get_db()
    oid = _valid_id(task_id)
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    updates["updated_at"] = datetime.now(timezone.utc)
    result = await db.tasks.find_one_and_update(
        {"_id": oid},
        {"$set": updates},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return _serialize(result)


async def delete_task(task_id: str) -> dict:
    db = get_db()
    oid = _valid_id(task_id)
    result = await db.tasks.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"deleted": True, "id": task_id}


async def get_labels() -> List[str]:
    db = get_db()
    labels = await db.tasks.distinct("labels")
    return sorted([l for l in labels if l])
