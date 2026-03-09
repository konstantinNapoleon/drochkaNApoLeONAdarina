import json
import sqlite3
import os

JSON_FILE = "database.json.hh"  # Твой старый файл
SQLITE_FILE = "users_database.db" # Твой новый файл

def migrate():
    if not os.path.exists(JSON_FILE):
        print(f"❌ Файл {JSON_FILE} не найден. Миграция отменена.")
        return

    # 1. Читаем данные из старого JSON
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        try:
            users_db = json.load(f)
        except json.JSONDecodeError:
            print(f"❌ Ошибка чтения {JSON_FILE}. Файл поврежден или пуст.")
            return

    # 2. Подключаемся к SQLite (создастся новый файл)
    conn = sqlite3.connect(SQLITE_FILE)
    cursor = conn.cursor()

    # 3. Создаем ПРАВИЛЬНУЮ таблицу для твоего main.py
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            data TEXT
        )
    """)
    
    # 4. Переносим данные
    count = 0
    for user_id_str, data in users_db.items():
        # Вставляем данные целиком как JSON-строку в колонку data
        cursor.execute("""
            INSERT INTO users (user_id, data)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET data=excluded.data
        """, (str(user_id_str), json.dumps(data, ensure_ascii=False)))
        
        count += 1

    # 5. Сохраняем изменения и закрываем соединение
    conn.commit()
    conn.close()
    
    print(f"✅ Миграция успешно завершена! Перенесено пользователей: {count}.")
    print(f"📁 Новая база данных: {SQLITE_FILE} готова для работы с main.py.")

if __name__ == "__main__":
    migrate()
