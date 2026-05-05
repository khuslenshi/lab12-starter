import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bson import ObjectId
from fastapi import HTTPException


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_task_doc(overrides: dict = {}) -> dict:
    oid = ObjectId()
    now = datetime.now(timezone.utc)
    base = {
        "_id": oid,
        "title": "Test Task",
        "description": "Test description",
        "priority": "medium",
        "status": "todo",
        "due_date": None,
        "labels": ["work"],
        "created_at": now,
        "updated_at": now,
    }
    base.update(overrides)
    return base


# ── Import services with mocked DB ───────────────────────────────────────────

@pytest.fixture(autouse=True)
def mock_db():
    """Patch get_db so every test uses a fresh AsyncMock collection."""
    mock_collection = MagicMock()
    mock_database = MagicMock()
    mock_database.tasks = mock_collection
    with patch("services.get_db", return_value=mock_database):
        yield mock_collection


# ── _serialize ───────────────────────────────────────────────────────────────

def test_serialize_returns_response():
    import services
    doc = make_task_doc()
    result = services._serialize(doc)
    assert result.id == str(doc["_id"])
    assert result.title == doc["title"]
    assert result.priority == "medium"
    assert result.status == "todo"
    assert result.labels == ["work"]


# ── _valid_id ─────────────────────────────────────────────────────────────────

def test_valid_id_accepts_valid_objectid():
    import services
    oid = ObjectId()
    result = services._valid_id(str(oid))
    assert result == oid


def test_valid_id_raises_on_invalid():
    import services
    with pytest.raises(HTTPException) as exc:
        services._valid_id("not-an-id")
    assert exc.value.status_code == 400


# ── create_task ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_task_success(mock_db):
    import services
    from models import TaskCreate

    doc = make_task_doc()
    mock_db.insert_one = AsyncMock(return_value=MagicMock(inserted_id=doc["_id"]))

    data = TaskCreate(title="Test Task", labels=["work"])
    result = await services.create_task(data)

    assert result.title == "Test Task"
    mock_db.insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_create_task_sets_timestamps(mock_db):
    import services
    from models import TaskCreate

    oid = ObjectId()
    mock_db.insert_one = AsyncMock(return_value=MagicMock(inserted_id=oid))

    data = TaskCreate(title="Timestamp Test")
    result = await services.create_task(data)

    assert result.created_at is not None
    assert result.updated_at is not None


# ── get_task ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_task_found(mock_db):
    import services

    doc = make_task_doc()
    mock_db.find_one = AsyncMock(return_value=doc)

    result = await services.get_task(str(doc["_id"]))
    assert result.id == str(doc["_id"])


@pytest.mark.asyncio
async def test_get_task_not_found(mock_db):
    import services

    mock_db.find_one = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await services.get_task(str(ObjectId()))
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_task_invalid_id(mock_db):
    import services

    with pytest.raises(HTTPException) as exc:
        await services.get_task("invalid-id")
    assert exc.value.status_code == 400


# ── update_task ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_task_success(mock_db):
    import services
    from models import TaskUpdate

    doc = make_task_doc({"status": "in_progress"})
    mock_db.find_one_and_update = AsyncMock(return_value=doc)

    result = await services.update_task(str(doc["_id"]), TaskUpdate(status="in_progress"))
    assert result.status == "in_progress"


@pytest.mark.asyncio
async def test_update_task_not_found(mock_db):
    import services
    from models import TaskUpdate

    mock_db.find_one_and_update = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await services.update_task(str(ObjectId()), TaskUpdate(status="done"))
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_task_no_fields(mock_db):
    import services
    from models import TaskUpdate

    with pytest.raises(HTTPException) as exc:
        await services.update_task(str(ObjectId()), TaskUpdate())
    assert exc.value.status_code == 400


# ── delete_task ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_task_success(mock_db):
    import services

    oid = ObjectId()
    mock_db.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))

    result = await services.delete_task(str(oid))
    assert result["deleted"] is True
    assert result["id"] == str(oid)


@pytest.mark.asyncio
async def test_delete_task_not_found(mock_db):
    import services

    mock_db.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))

    with pytest.raises(HTTPException) as exc:
        await services.delete_task(str(ObjectId()))
    assert exc.value.status_code == 404


# ── get_labels ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_labels_returns_sorted(mock_db):
    import services

    mock_db.distinct = AsyncMock(return_value=["work", "personal", "urgent", ""])

    result = await services.get_labels()
    assert result == ["personal", "urgent", "work"]  # sorted, empty filtered
    assert "" not in result


# ── Priority & Status validation ──────────────────────────────────────────────

def test_task_default_priority_and_status():
    from models import TaskCreate
    task = TaskCreate(title="Defaults test")
    assert task.priority == "medium"
    assert task.status == "todo"


def test_task_labels_default_empty():
    from models import TaskCreate
    task = TaskCreate(title="No labels")
    assert task.labels == []
