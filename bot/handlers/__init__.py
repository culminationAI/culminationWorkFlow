"""Bot handlers package."""

from aiogram import Router

from handlers.commands import router as commands_router
from handlers.chat import router as chat_router


def setup_routers() -> Router:
    """Create main router with all sub-routers."""
    main_router = Router()
    # Commands first (higher priority than catch-all text handler)
    main_router.include_router(commands_router)
    main_router.include_router(chat_router)
    return main_router
