import sqlite3
import psycopg2
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()
SQLITE_FILE = "users_database.db"
DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require', connect_timeout=10)


def migrate():
    sqlite_conn = sqlite3.connect(SQLITE_FILE)
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("SELECT user_id, data FROM users")
    rows = sqlite_cur.fetchall()
    total = len(rows)
    print(f"📦 Найдено: {total} юзеров. Начинаю перенос с пропуском проблемных записей...")

    pg_conn = None
    count = 0
    skipped = []

    for user_id, data_json in rows:
        try:
            if pg_conn is None or pg_conn.closed != 0:
                pg_conn = get_connection()
                pg_cur = pg_conn.cursor()

            # Пробуем вставить
            pg_cur.execute("""
        INSERT INTO users (user_id, data) VALUES (%s, %s)
        ON CONFLICT(user_id) DO UPDATE SET data = EXCLUDED.data
      """, (str(user_id), data_json))

            pg_conn.commit()
            count += 1
            if count % 10 == 0:
                print(f"🚀 Прогресс: {count}/{total}")

        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            print(f"⚠️ Юзер {user_id} слишком тяжелый (разрыв связи). ПРОПУСКАЮ.")
            skipped.append(user_id)
            if pg_conn:
                try:
                    pg_conn.close()
                except:
                    pass
            pg_conn = None  # Чтобы на следующем юзере создалось новое соединение
            continue  # Идем к следующему игроку!

        except Exception as e:
            print(f"❌ Ошибка на {user_id}: {e}")
            if pg_conn: pg_conn.rollback()
            skipped.append(user_id)

    print(f"\n✅ ГОТОВО!")
    print(f"Успешно перенесено: {count}")
    print(f"Пропущено (слишком большие): {len(skipped)}")
    if skipped:
        print(f"Список пропущенных ID: {skipped}")

    sqlite_conn.close()
    if pg_conn: pg_conn.close()


if __name__ == "__main__":
    migrate()