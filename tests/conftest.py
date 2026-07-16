import os

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from app.infrastructure.database.base import Base
from app.infrastructure.database.repositories.sqlalchemy import SqlAlchemyUnitOfWorkFactory


@pytest.fixture(scope="session")
def database_url() -> str:
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://avix:avix@localhost:5432/avix_test",
    )


@pytest.fixture(scope="session")
def redis_url() -> str:
    return os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1")


@pytest.fixture(scope="session", autouse=True)
async def prepare_database(database_url):
    engine = create_async_engine(database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    yield


@pytest.fixture
async def uow_factory(database_url):
    factory = SqlAlchemyUnitOfWorkFactory(database_url)
    yield factory
    await factory.dispose()
