from handlers import start, help, links, language
from aiogram import Bot, Dispatcher, Router
import asyncio
from config import API_TOKEN
from db.database import BotDB
from tools.handle_old_files import run_delete_files_periodically
from workers import download_link, download_playlist, process_file_links

db = BotDB()

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

router = Router()


dp.include_router(start.router)
dp.include_router(language.router)
dp.include_router(help.router)
dp.include_router(links.router)
dp.include_router(download_link.router)
dp.include_router(download_playlist.router)
dp.include_router(process_file_links.router)


async def main():
    asyncio.create_task(run_delete_files_periodically(db))
    await dp.start_polling(bot)

if __name__ == "__main__":
    db._initialize_db()
    asyncio.run(main())
