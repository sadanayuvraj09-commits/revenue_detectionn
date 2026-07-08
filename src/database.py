from motor.motor_asyncio import AsyncIOMotorClient
import certifi

from .config import get_settings


settings = get_settings()

if not settings.mongo_uri:
    raise RuntimeError("MONGO_URI is not configured. Add it to your .env file.")

# Use certifi's CA bundle for TLS to avoid local OpenSSL/CA issues
client = AsyncIOMotorClient(
    settings.mongo_uri,
    serverSelectionTimeoutMS=3000,
    maxPoolSize=10,
    minPoolSize=1,
    tls=True,
    tlsCAFile=certifi.where(),
)
db = client[settings.mongo_db_name]
