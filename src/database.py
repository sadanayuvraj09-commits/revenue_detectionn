from motor.motor_asyncio import AsyncIOMotorClient

from .config import get_settings


settings = get_settings()

if not settings.mongo_uri:
    raise RuntimeError("MONGO_URI is not configured. Add it to your .env file.")

client = AsyncIOMotorClient(settings.mongo_uri)
db = client[settings.mongo_db_name]
