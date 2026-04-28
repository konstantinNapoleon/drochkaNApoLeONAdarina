import random
import datetime
import psycopg2

from .pass_data import (
    SEASON_ID,
    DAILY_TASK_POOL,
    DAILY_TASKS_COUNT,
    DAILY_BONUS_REWARD,
)

DATABASE_URL = None


def setup_pass_db(database_url: str):
    global DATABASE_URL
    DATABASE_URL = database_url


def get_db_connection():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL не задан для ivent/pass_db.py")
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def today_date():
    return datetime.date.today()


async def get_or_create_pass_user(user_id: int):
    uid = str(user_id)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
                SELECT user_id, season_id, peaches, is_ultra, bonus_last_claim_date
                FROM ivent_pass_users
                WHERE user_id = %s AND season_id = %s
                LIMIT 1
            """, (uid, SEASON_ID))

        row = cursor.fetchone()

        if row:
            return {
                "user_id": row[0],
                "season_id": row[1],
                "peaches": row[2],
                "is_ultra": row[3],
                "bonus_last_claim_date": str(row[4]) if row[4] else None,
            }

        cursor.execute("""
                INSERT INTO ivent_pass_users (
                    user_id, season_id, peaches, is_ultra, bonus_last_claim_date
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING user_id, season_id, peaches, is_ultra, bonus_last_claim_date
            """, (uid, SEASON_ID, 0, False, None))

        row = cursor.fetchone()
        conn.commit()

        return {
            "user_id": row[0],
            "season_id": row[1],
            "peaches": row[2],
            "is_ultra": row[3],
            "bonus_last_claim_date": str(row[4]) if row[4] else None,
        }

    finally:
        cursor.close()
        conn.close()


async def get_pass_user(user_id: int):
    return await get_or_create_pass_user(user_id)


async def update_pass_user(user_id: int, updates: dict):
    uid = str(user_id)

    allowed_fields = {
        "peaches",
        "is_ultra",
        "bonus_last_claim_date",
    }

    set_parts = []
    values = []

    for key, value in updates.items():
        if key in allowed_fields:
            set_parts.append(f"{key} = %s")
            values.append(value)

    set_parts.append("updated_at = NOW()")

    if not values:
        return False

    values.extend([uid, SEASON_ID])

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = f"""
                UPDATE ivent_pass_users
                SET {", ".join(set_parts)}
                WHERE user_id = %s AND season_id = %s
            """
        cursor.execute(query, tuple(values))
        conn.commit()
        return True
    finally:
        cursor.close()
        conn.close()


async def add_peaches(user_id: int, amount: int):
    user = await get_pass_user(user_id)
    new_peaches = int(user.get("peaches", 0)) + int(amount)
    await update_pass_user(user_id, {"peaches": new_peaches})
    return new_peaches


async def get_claimed_levels(user_id: int):
    uid = str(user_id)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
                SELECT level
                FROM ivent_pass_claims
                WHERE user_id = %s AND season_id = %s
                ORDER BY level ASC
            """, (uid, SEASON_ID))

        rows = cursor.fetchall()
        return [row[0] for row in rows]
    finally:
        cursor.close()
        conn.close()


async def is_level_claimed(user_id: int, level: int):
    uid = str(user_id)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
                SELECT 1
                FROM ivent_pass_claims
                WHERE user_id = %s AND season_id = %s AND level = %s
                LIMIT 1
            """, (uid, SEASON_ID, level))

        return cursor.fetchone() is not None
    finally:
        cursor.close()
        conn.close()


async def claim_level(user_id: int, level: int):
    uid = str(user_id)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
                INSERT INTO ivent_pass_claims (user_id, season_id, level)
                VALUES (%s, %s, %s)
                            ON CONFLICT (user_id, season_id, level) DO NOTHING
        """, (uid, SEASON_ID, level))

        conn.commit()
        return True
    finally:
        cursor.close()
        conn.close()


async def get_today_tasks(user_id: int):
    uid = str(user_id)
    today = today_date()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, task_id, task_text, progress, target, reward, is_completed, claimed
            FROM ivent_pass_daily_tasks
            WHERE user_id = %s AND season_id = %s AND task_date = %s
            ORDER BY id ASC
        """, (uid, SEASON_ID, today))

        rows = cursor.fetchall()

        tasks = []
        for row in rows:
            tasks.append({
                "id": row[0],
                "task_id": row[1],
                "text": row[2],
                "progress": row[3],
                "target": row[4],
                "reward": row[5],
                "is_completed": row[6],
                "claimed": row[7],
            })

        return tasks
    finally:
        cursor.close()
        conn.close()


async def create_daily_tasks(user_id: int):
    uid = str(user_id)
    today = today_date()

    selected_tasks = random.sample(DAILY_TASK_POOL, DAILY_TASKS_COUNT)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        for task in selected_tasks:
            cursor.execute("""
                INSERT INTO ivent_pass_daily_tasks (
                    user_id, season_id, task_date, task_id, task_text,
                    progress, target, reward, is_completed, claimed
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                uid,
                SEASON_ID,
                today,
                task["id"],
                task["text"],
                0,
                task["target"],
                task["reward"],
                False,
                False
            ))

        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return await get_today_tasks(user_id)


async def get_or_create_today_tasks(user_id: int):
    tasks = await get_today_tasks(user_id)
    if tasks:
        return tasks
    return await create_daily_tasks(user_id)


async def update_task_progress(task_row_id: int, progress: int, is_completed: bool):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE ivent_pass_daily_tasks
            SET progress = %s, is_completed = %s
            WHERE id = %s
        """, (progress, is_completed, task_row_id))

        conn.commit()
        return True
    finally:
        cursor.close()
        conn.close()


async def claim_daily_bonus(user_id: int):
    from .pass_data import DAILY_BONUS_REWARD, ULTRA_PASS_DAILY_BONUS

    user = await get_pass_user(user_id)
    today = today_date()

    last_claim = user.get("bonus_last_claim_date")
    if last_claim == str(today):
        return False, 0, user.get("peaches", 0)

    bonus_to_add = DAILY_BONUS_REWARD
    if user.get("is_ultra"):
        bonus_to_add += ULTRA_PASS_DAILY_BONUS

    new_peaches = int(user.get("peaches", 0)) + bonus_to_add

    await update_pass_user(user_id, {
        "peaches": new_peaches,
        "bonus_last_claim_date": today
    })

    return True, bonus_to_add, new_peaches


async def has_claimed_daily_bonus(user_id: int):
    user = await get_pass_user(user_id)
    return user.get("bonus_last_claim_date") == str(today_date())


async def set_ultra_pass(user_id: int, value: bool = True):
    await update_pass_user(user_id, {"is_ultra": value})
    return True

