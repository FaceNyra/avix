from aiogram import Dispatcher

from .start import router as start_router

__all__ = ["setup_routers"]


def setup_routers(dp: Dispatcher) -> None:
	dp.include_router(start_router)
