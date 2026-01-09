import asyncio
from app.db.session import get_database_url, get_engine
from sqlalchemy import text

async def test_connection():
    url = get_database_url()
    print(f"Database URL: {url[:30]}...{url[-20:]}")
    
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ Database connected successfully!")
            print(f"Result: {result.fetchone()}")
    except Exception as e:
        print(f"❌ Connection failed: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
