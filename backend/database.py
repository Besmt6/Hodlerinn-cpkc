"""
Database Module
Handles MongoDB connection and provides database access.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URL, DB_NAME

# MongoDB connection
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Demo database (separate collections for demo mode)
demo_db = client[DB_NAME + "_demo"]

async def ping_database():
    """Check database connectivity"""
    try:
        await db.command('ping')
        return True
    except Exception:
        return False

async def get_collection(collection_name: str, use_demo: bool = False):
    """Get a collection from the appropriate database"""
    if use_demo:
        return demo_db[collection_name]
    return db[collection_name]
