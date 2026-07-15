from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart

from infrastructure import User, UserRepository

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
	user_repository = UserRepository()
	await user_repository.create_user(User(
		tg_id=message.from_user.id,
		username=message.from_user.username,
		first_name=message.from_user.first_name,
		last_name=message.from_user.last_name,
	))
	await message.answer("Welcome to the bot")
