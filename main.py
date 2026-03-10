import asyncio
import logging
import json
import sqlite3
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

load_dotenv()

# --- Импорты роутеров ---
from handlers.start import router as start_router
from handlers.droch import router as droch_router
from handlers.ferma import router as ferma_router
from handlers.shop import router as shop_router
from inventory.commands import router as inventory_router
from handlers.oil import router as oil_router
from handlers.itemgive import router as itemgive_router
from handlers.bonus import router as bonus_router
from handlers.id import router as id_router
from handlers.vidacha import router as vidacha_router
from inventory.inventar import router as inventar_router
from tools.admin import router as admin_router
from games.gamecub import router as gamecub_router
from farm.topdrochek import router as topdrochek_router
from tools.reklama import router as reklama_router
from dataIT.bonuscode import router as bonuscode_router
from handlers.bafus import router as bafus_router
from inventory.useitem import router as useitem_router


# --- НАСТРОЙКИ БОТА ---
TOKEN = os.getenv("BOT_TOKEN")

# Имя файла базы данных SQLite
DB_NAME = "/data/users_database.db"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


# --- ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ (SQLite) ---

def init_db():
    """Создает таблицу в SQLite, если ее еще нет"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Таблица users хранит все данные в формате JSON-строк для обратной совместимости
    # с твоими остальными файлами (роутерами)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            data TEXT
        )
    """)
    conn.commit()
    conn.close()
    logger.info(f"База данных '{DB_FILE}' инициализирована.")


async def get_user(user_id, username=None):
    """
  Получает данные пользователя из SQLite.
  Возвращает словарь (dict), точно так же, как было раньше при JSON.
  """
    uid = str(user_id)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT data FROM users WHERE user_id = ?", (uid,))
    row = cursor.fetchone()

    if row:
        user_data = json.loads(row[0])
        # Если ник обновился
        if username and user_data.get("username") != username:
            user_data["username"] = username
            # Сразу сохраняем обновление ника
            cursor.execute("UPDATE users SET data = ? WHERE user_id = ?",
                           (json.dumps(user_data, ensure_ascii=False), uid))
            conn.commit()
    else:
        # Новый пользователь
        user_data = {
            "balance": 0,
            "inventory": [],
            "masturbations_count": 0,
            "username": username
        }
        cursor.execute("INSERT INTO users (user_id, data) VALUES (?, ?)",
                       (uid, json.dumps(user_data, ensure_ascii=False)))
        conn.commit()

    conn.close()
    return user_data


async def save_db(user_id=None, user_data=None):
    """
  Сохраняет данные конкретного пользователя в SQLite.

  ВАЖНО ДЛЯ ТВОИХ ФАЙЛОВ: Раньше функция save_db() сохраняла весь JSON целиком без аргументов.
  Так как в разных твоих файлах (shop.py, droch.py) может вызываться просто save_db(),
  эта функция оставлена для совместимости, но теперь она ничего не делает, если вызвана без аргументов.
  Чтобы данные сохранялись, в других файлах нужно вызывать: save_db(user_id, user_data)
  """
    if user_id is None or user_data is None:
        logger.warning(
            "Вызвана функция save_db() без аргументов. В SQLite нужно передавать user_id и user_data. Если это старый код, он не сохранит данные!")
        return

    uid = str(user_id)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (user_id, data) 
        VALUES (?, ?) 
        ON CONFLICT(user_id) DO UPDATE SET data = excluded.data
    """, (uid, json.dumps(user_data, ensure_ascii=False)))

    conn.commit()
    conn.close()


async def get_all_users():
    """
  Возвращает всех пользователей в виде словаря {user_id: user_data}.
  Нужно для топов и админ-команд.
  """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, data FROM users")
    rows = cursor.fetchall()
    conn.close()

    all_users = {}
    for row in rows:
        uid = row[0]
        data = json.loads(row[1])
        all_users[uid] = data

    return all_users


# --- ГЛАВНАЯ ФУНКЦИЯ ЗАПУСКА БОТА ---

async def main():
    init_db()

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    dp["get_user"] = get_user
    dp["save_db"] = save_db

    dp.include_router(start_router)
    dp.include_router(droch_router)
    dp.include_router(gamecub_router)
    dp.include_router(shop_router)
    dp.include_router(inventory_router)
    dp.include_router(oil_router)
    dp.include_router(itemgive_router)
    dp.include_router(bonus_router)
    dp.include_router(id_router)
    dp.include_router(vidacha_router)
    dp.include_router(inventar_router)
    dp.include_router(admin_router)
    dp.include_router(ferma_router)
    dp.include_router(topdrochek_router)
    dp.include_router(reklama_router)
    dp.include_router(bonuscode_router)
    dp.include_router(bafus_router)
    dp.include_router(useitem_router)

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("🚀 БОТ ЗАПУЩЕН!")

    await dp.start_polling(
        bot,
        get_user=get_user,
        save_db=save_db,
        get_all_users=get_all_users
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Бот остановлен вручную.")
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}", exc_info=True)