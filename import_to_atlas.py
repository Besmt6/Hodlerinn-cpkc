import json
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'hodler_inn')

async def import_data():
    print(f"Connecting to Atlas: {MONGO_URL[:50]}...")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    dump_dir = '/app/hodler_inn_dump'
    
    collections = [
        'blocked_rooms', 'bookings', 'email_alert_settings', 'employees',
        'expected_arrivals', 'guests', 'notification_state', 
        'pending_access_requests', 'rooms', 'settings', 'sync_history',
        'turned_away_guests'
    ]
    
    for collection_name in collections:
        file_path = os.path.join(dump_dir, f'{collection_name}.json')
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if data:
                # Clear existing data in collection
                await db[collection_name].delete_many({})
                
                # Remove _id fields if they exist (let MongoDB generate new ones)
                for doc in data:
                    if '_id' in doc:
                        del doc['_id']
                
                # Insert new data
                result = await db[collection_name].insert_many(data)
                print(f"✅ {collection_name}: Imported {len(result.inserted_ids)} documents")
            else:
                print(f"⏭️ {collection_name}: Empty, skipped")
        else:
            print(f"❌ {collection_name}: File not found")
    
    client.close()
    print("\n✅ Import complete!")

asyncio.run(import_data())
