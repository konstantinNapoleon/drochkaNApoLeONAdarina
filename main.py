import asyncio
import logging
import json
import psycopg2
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

load_dotenv()

# --- Импорты роутеров ---
from handlers.referal import router as referal_router
from handlers.droch import router as droch_router
from handlers.trade import router as trade_router
from handlers.shop import router as shop_router
from inventory.commands import router as inventory_router
from games.case import router as case_router
from handlers.itemgive import router as itemgive_router
from handlers.bonus import router as bonus_router
from handlers.id import router as id_router
from handlers.vidacha import router as vidacha_router
from inventory.inventar import router as inventar_router
from tools.admin import router as admin_router
from games.gamecub import router as gamecub_router
from farm.topdrochek import router as topdrochek_router
from tools.reklama import router as reklama_router
from handlers.bafus import router as bafus_router
from inventory.xlame import router as xlame_router
from tools.refprog import router as refprog_router
from handlers.etel import router as etel_router
from games.cybik import router as cybik_router
from games.igram import router as igram_router
from handlers.ivent import router as ivent_router
from inventory.backpack import router as backpack_router

# --- НАСТРОЙКИ БОТА ---
TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


# --- ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ (PostgreSQL / Supabase) ---

def get_db_connection():
    """Создает подключение к облачной базе Supabase"""
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
    """Создает таблицу в облаке, если ее еще нет"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                data TEXT
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Облачная база данных успешно инициализирована.")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")

async def get_user(user_id, username=None):
    """Получает данные пользователя из облака."""
    uid = str(user_id)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT data FROM users WHERE user_id = %s", (uid,))
        row = cursor.fetchone()

        if row:
            user_data = json.loads(row[0])
            if username and user_data.get("username") != username:
                user_data["username"] = username
                cursor.execute("UPDATE users SET data = %s WHERE user_id = %s",
                              (json.dumps(user_data, ensure_ascii=False), uid))
                conn.commit()
        else:
            user_data = {
                "balance": 0,
                "inventory": [],
                "masturbations_count": 0,
                "username": username
            }
            cursor.execute("INSERT INTO users (user_id, data) VALUES (%s, %s)",
                          (uid, json.dumps(user_data, ensure_ascii=False)))
            conn.commit()

        cursor.close()
        conn.close()
        return user_data
    except Exception as e:
        logger.error(f"Ошибка в get_user: {e}")
        return None

async def save_db(user_id=None, user_data=None):
    """Сохраняет данные конкретного пользователя в облако."""
    if user_id is None or user_data is None:
        logger.warning("Вызвана функция save_db() без аргументов.")
        return

    uid = str(user_id)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users (user_id, data) 
            VALUES (%s, %s) 
            ON CONFLICT(user_id) DO UPDATE SET data = EXCLUDED.data
        """, (uid, json.dumps(user_data, ensure_ascii=False)))

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка в save_db: {e}")

async def get_all_users():
    """Возвращает всех пользователей из облака."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, data FROM users")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        all_users = {}
        for row in rows:
            uid = row[0]
            data = json.loads(row[1])
            all_users[uid] = data

        return all_users
    except Exception as e:
        logger.error(f"Ошибка в get_all_users: {e}")
        return {}


# --- ГЛАВНАЯ ФУНКЦИЯ ЗАПУСКА БОТА ---

async def main():
    init_db()

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    # Прокидываем функции в middleware/handlers
    dp["get_user"] = get_user
    dp["save_db"] = save_db

    dp.include_router(referal_router)
    dp.include_router(droch_router)
    dp.include_router(gamecub_router)
    dp.include_router(shop_router)
    dp.include_router(inventory_router)
    dp.include_router(case_router)
    dp.include_router(itemgive_router)
    dp.include_router(bonus_router)
    dp.include_router(id_router)
    dp.include_router(vidacha_router)
    dp.include_router(inventar_router)
    dp.include_router(admin_router)
    dp.include_router(trade_router)
    dp.include_router(topdrochek_router)
    dp.include_router(reklama_router)
    dp.include_router(bafus_router)
    dp.include_router(xlame_router)
    dp.include_router(refprog_router)
    dp.include_router(etel_router)
    dp.include_router(cybik_router)
    dp.include_router(igram_router)
    dp.include_router(ivent_router)
    dp.include_router(backpack_router)

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("🚀 БОТ ЗАПУЩЕН НА ОБЛАЧНОЙ БАЗЕ (SUPABASE)!")

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
        logger.info("🛑 Бот остановлен.")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)