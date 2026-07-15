from aiogram import Bot, Dispatcher
from core.config import settings

import logging
import asyncio

from bot.middlewares import DbSessionMiddleware
from bot.routers import setup_routers
from infrastructure.database.session import create_db, db


async def main():
	logging.basicConfig(level=logging.INFO)

	bot = Bot(token=settings.token)
	dp = Dispatcher()

	dp.update.middleware(DbSessionMiddleware())
	setup_routers(dp)

	await create_db()

	try:
		await bot.delete_webhook(drop_pending_updates=True)
		await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
	finally:
		await db.close()


if __name__ == "__main__":
	try:
		logging.basicConfig(level=logging.INFO)
		asyncio.run(main())
	except Exception as e:
		logging.error(f"Error: {e}")
		raise e
