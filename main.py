import asyncio
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import close_pool, create_pool, init_db, seed_operation_catalog
from handlers import register_handlers

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    await create_pool()
    await init_db()
    await seed_operation_catalog()
    register_handlers(dp)

    me = await bot.get_me()
    print(f"Бот подключился: @{me.username}")

    try:
        await dp.start_polling(bot)
    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(main())
