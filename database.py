import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from models import Base

load_dotenv()

DATABASE = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE)

SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)