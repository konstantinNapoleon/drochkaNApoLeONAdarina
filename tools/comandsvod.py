import sqlite3
import json
from aiogram import Router, types

router = Router()

DB_PATH = "users_database.db"


def init_db():
    """Инициализация базы данных при запуске бота"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            data TEXT
        )
    ''')
    conn.commit()
    conn.close()


def get_user(user_id: int, username: str = None):
    """Получение данных пользователя из SQLite"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT data FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if row:
        user_data = json.loads(row[0])
    else:
        # Стандартный шаблон нового игрока
        user_data = {
            "registered": False,
            "balance": 0,
            "oil": 0,
            "level": 1,
            "xp": 0,
            "inventory": {},
            "referral_count": 0,
            "last_bonus_time": 0,
            "oil_place_id": 0,
            "oil_ban_until": 0,
            "last_oil_mine": 0,
            "chats_data": {}
        }
        # Создаем запись, если юзера нет
        cursor.execute("INSERT INTO users (user_id, username, data) VALUES (?, ?, ?)",
                       (user_id, username, json.dumps(user_data)))
        conn.commit()

    conn.close()
    return user_data


def save_db(user_id: int, user_data: dict):
    """Сохранение данных пользователя в SQLite"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET data = ? WHERE user_id = ?",
                   (json.dumps(user_data, ensure_ascii=False), user_id))
    conn.commit()
    conn.close()


def router():
    return None