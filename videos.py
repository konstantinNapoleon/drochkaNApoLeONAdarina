import sqlite3
import psycopg2
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

SQLITE_FILE = "users_database.db"
DATABASE_URL = os.getenv("DATABASE_URL")


def get_pg_connection():
    """Функция для создания нового подключения"""
    return psycopg2.connect(DATABASE_URL, sslmode='require', connect_timeout=10)


def migrate():
    if not os.path.exists(SQLITE_FILE):
        print(f"❌ Файл {SQLITE_FILE} не найден!")
        return

    sqlite_conn = sqlite3.connect(SQLITE_FILE)
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("SELECT user_id, data FROM users")
    rows = sqlite_cur.fetchall()
    total = len(rows)

    print(f"📦 Найдено пользователей: {total}. Начинаю перенос...")

    pg_conn = None
    pg_cur = None
    count = 0

    for user_id, data_json in rows:
        retry = True
        while retry:
            try:
                # Если соединения нет или оно закрыто — создаем заново
                if pg_conn is None or pg_conn.closed != 0:
                    print("🔄 Подключаюсь к Supabase (Сеул далеко, ждем...)...")
                    pg_conn = get_pg_connection()
                    pg_cur = pg_conn.cursor()

                data = json.loads(data_json)

                pg_cur.execute("""
          INSERT INTO users (user_id, data) 
          VALUES (%s, %s) 
          ON CONFLICT(user_id) DO UPDATE SET data = EXCLUDED.data
        """, (str(user_id), json.dumps(data, ensure_ascii=False)))

                pg_conn.commit()
                count += 1
                if count % 10 == 0 or count == total:
                    print(f"✅ Перенесено: {count}/{total}")

                retry = False  # Успешно, выходим из цикла retry

            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                print(f"📡 Связь оборвалась на юзере {user_id}. Пробую еще раз через 3 сек...")
                if pg_conn:
                    try:
                        pg_conn.close()
                    except:
                        pass
                pg_conn = None  # Сбрасываем, чтобы переподключиться
                time.sleep(3)

            except Exception as e:
                print(f"❌ Критическая ошибка на {user_id}: {e}")
                retry = False  # Пропускаем этого юзера

    # Закрываем всё
    sqlite_cur.close()
    sqlite_conn.close()
    if pg_conn:
        pg_cur.close()
        pg_conn.close()

    print(f"\n🎉 ПЕРЕНОС ЗАВЕРШЕН! Успешно: {count} из {total}")


if __name__ == "__main__":
    migrate()