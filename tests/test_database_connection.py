import pytest

from src.database import db


@pytest.mark.asyncio
async def test_mongo_insert_and_delete():
    result = await db.activity_logs.insert_one({"test": "pytest_connection_check"})
    assert result.inserted_id is not None

    # Clean up: remove the test document so it doesn't pollute real data
    delete_result = await db.activity_logs.delete_one({"_id": result.inserted_id})
    assert delete_result.deleted_count == 1


@pytest.mark.asyncio
async def test_mongo_connection_lists_collections():
    collections = await db.list_collection_names()
    assert isinstance(collections, list)