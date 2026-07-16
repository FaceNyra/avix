from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from context_async_sqlalchemy import (
	commit_all_sessions,
	init_db_session_ctx,
	is_context_initiated,
	reset_db_session_ctx,
	rollback_all_sessions,
)


class DbSessionMiddleware(BaseMiddleware):
	async def __call__(
		self,
		handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
		event: TelegramObject,
		data: dict[str, Any],
	) -> Any:
		if is_context_initiated():
			return await handler(event, data)

		token = init_db_session_ctx()
		try:
			result = await handler(event, data)
			await commit_all_sessions()
			return result
		except Exception:
			await rollback_all_sessions()
			raise
		finally:
			await reset_db_session_ctx(token)
