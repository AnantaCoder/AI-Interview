import asyncio
import os
import sys

# Add the backend dir to the path so app can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import get_engine
from sqlalchemy import text

async def migrate():
    engine = get_engine()
    async with engine.begin() as conn:
        print("Adding columns to 'users' table...")
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS address VARCHAR(500)"))
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number VARCHAR(20)"))
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE"))
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS skills JSON DEFAULT '[]'::json"))
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS job_role VARCHAR(255)"))
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS year_of_experience INTEGER DEFAULT 0"))
        print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
