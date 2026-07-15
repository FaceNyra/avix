from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from context_async_sqlalchemy import db_session

from infrastructure.database.models import User
from infrastructure.database.session import db


class UserRepository:
	async def _session(self) -> AsyncSession:
		return await db_session(db)

	async def get_user(self, tg_id: int) -> User | None:
		session = await self._session()
		result = await session.execute(select(User).where(User.tg_id == tg_id))
		return result.scalar_one_or_none()

	async def create_user(self, user: User) -> User:
		session = await self._session()
		existing = await self.get_user(user.tg_id)
		if existing:
			return existing

		session.add(user)
		await session.flush()
		return user
