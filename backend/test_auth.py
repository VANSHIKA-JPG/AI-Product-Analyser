import asyncio
import sys
sys.path.insert(0, ".")

from app.api.auth import register
from app.schemas.schemas import UserCreate
from app.database import AsyncSessionLocal

async def test():
    user_data = UserCreate(username="testuser123", email="test123abc@test.com", password="Password1!")
    async with AsyncSessionLocal() as db:
        try:
            res = await register(user_data, db)
            print("OK", res.user.username)
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
