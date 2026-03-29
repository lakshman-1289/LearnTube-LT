import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict

class DBService:
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self._initialize()

    def _initialize(self):
        try:
            mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
            db_name = os.getenv("DB_NAME", "learntube_db")
            collection_name = os.getenv("COLLECTION_NAME", "courses")

            self.client = AsyncIOMotorClient(mongo_uri)
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]
            
            # Create a unique index on videoId for fast querying
            # In a truly robust setup, we might want to ensure this isn't called on every init
            # but for our use case, Motor handles index requests smoothly.
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.collection.create_index("video_id", unique=True))
            except RuntimeError:
                pass # Event loop not running yet

        except Exception as e:
            print(f"[DB INIT ERROR] Failed to connect to MongoDB: {e}")

    async def get_cached_course(self, video_id: str) -> Optional[Dict]:
        """
        Retrieves a cached course completely if it exists based on the YouTube video ID.
        """
        if self.collection is None:
            return None
        
        try:
            document = await self.collection.find_one({"video_id": video_id})
            if document:
                # Remove MongoDB _id as it cannot be json serialized natively by FastAPI
                document.pop("_id", None)
                course_data = document.get("course_data")
                print(f"✅ Cache hit for video_id: {video_id}")
                return document
            return None
        except Exception as e:
            print(f"[DB READ ERROR]: {e}")
            return None

    async def cache_course(self, video_id: str, youtube_url: str, title: str, transcript_length: int, chapters: list, course_data: Dict) -> bool:
        """
        Stores the generated course output into the DB along with metadata.
        """
        if self.collection is None:
            return False
            
        try:
            document = {
                "video_id": video_id,
                "url": youtube_url,
                "title": title,
                "transcript_length": transcript_length,
                "chapters": chapters,
                "course_data": course_data
            }
            # Use update_one with upsert=True to avoid DuplicateKeyError collisions
            await self.collection.update_one(
                {"video_id": video_id},
                {"$set": document},
                upsert=True
            )
            print(f"📦 Successfully cached course for: {video_id}")
            return True
        except Exception as e:
            print(f"[DB WRITE ERROR]: {e}")
            return False

# Export a singleton instance 
db_service = DBService()
