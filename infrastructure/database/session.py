from sqlalchemy.ext.asyncio import (
	AsyncEngine,
	AsyncSession,
	async_sessionmaker,
	create_async_engine,
)
from context_async_sqlalchemy import DBConnect

from core.config import settings
from infrastructure.database.base import Base


def create_engine(host: str) -> AsyncEngine:
	return create_async_engine(
		f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
		f"@{host}:{settings.postgres_port}/{settings.postgres_db}",
		echo=True,
		pool_pre_ping=True,
	)


def create_session_maker(
	engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
	return async_sessionmaker(
		engine,
		class_=AsyncSession,
		expire_on_commit=False,
	)


db = DBConnect(
	engine_creator=create_engine,
	session_maker_creator=create_session_maker,
	host=settings.postgres_host,
)


async def create_db() -> None:
	maker = await db.session_maker()
	engine: AsyncEngine = maker.kw["bind"]
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
	maker = await db.session_maker()
	engine: AsyncEngine = maker.kw["bind"]
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.drop_all)
