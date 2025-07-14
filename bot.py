import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN
from routers import all_routers
# import logging

# logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Подключение модулей (роутеров)
for router in all_routers:
    # logging.info(f"Including router: {router.name if hasattr(router, 'name') else 'Unnamed Router'}")
    dp.include_router(router)

# Добавляем middleware для логирования всех обновлений (закомментировано)
# @dp.update.middleware()
# async def log_updates(handler, event, data):
#     logging.info(f"Received update: {event}")
#     return await handler(event, data)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
