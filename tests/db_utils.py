import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from aanvraagapp import models


async def delete_tables():
    """Delete all tables from the database - for testing only"""
    engine = create_async_engine("sqlite+aiosqlite:///./aanvraagapp.db")
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)
    await engine.dispose()


async def create_db_and_tables():
    """Create all tables in the database - for testing only"""
    engine = create_async_engine("sqlite+aiosqlite:///./aanvraagapp.db")
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    await engine.dispose()


async def init_db():
    """Initialize the database by creating all tables - for testing only"""
    print("Creating database tables...")
    await create_db_and_tables()
    print("Database tables created successfully!")


async def cleanup_db():
    """Clean up the database by dropping all tables - for testing only"""
    print("Dropping database tables...")
    await delete_tables()
    print("Database tables dropped successfully!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "teardown":
        asyncio.run(cleanup_db())
    elif len(sys.argv) > 1 and sys.argv[1] == "setup":
        asyncio.run(init_db())
    else:
        print("Error: Please specify 'setup' or 'teardown'")
        print("Usage: python -m tests.db_utils setup|teardown")
        sys.exit(1)