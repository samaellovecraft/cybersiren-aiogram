# Standard library imports
import asyncio
import logging

# Third-party library imports
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

# Local application specific imports
from config import API_TOKEN, DEFAULT_COMMANDS
from core.handlers import router as core_router
from quiz.handlers import router as quiz_router


async def main() -> None:
    logging.basicConfig(level=logging.DEBUG)

    bot = Bot(token=API_TOKEN, parse_mode=ParseMode.MARKDOWN)
    dp = Dispatcher()
    dp.include_routers(
        quiz_router,
        core_router # ! contains `echo` handler; place at the and to avoid overriding other handlers
    )

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(DEFAULT_COMMANDS)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
