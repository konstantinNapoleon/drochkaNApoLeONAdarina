import random
import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# --- ОБНОВЛЕННЫЕ ИМПОРТЫ ---
from .pass_data import (
    SEASON_ID,
    DAILY_TASK_POOL,
    DAILY_TASKS_COUNT,
    MEGA_PASS_TASKS_COUNT,  # Добавлено
    PASS_TIER_ULTRA,  # Добавлено
    PASS_TIER_MEGA,  # Добавлено
)

DATABASE_URL = None


# --- Твои функции подключения (без изменений) ---
def setup_pass_db(database_url: str):
    global DATABASE_URL
    DATABASE_URL = database_url


def get_db_connection():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL не задан для ivent/pass_db.py")
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def today_date():
    return datetime.date.today()


# --- ИЗМЕНЕННЫЕ ФУНКЦИИ ---

async def get_or_create_pass_user(user_id: int):
    """Изменено: работает с pass_tier и auto_claim_enabled вместо is_ultra."""
    uid = str(user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Запрашиваем новые поля pass_tier и auto_claim_enabled
        cursor.execute("""
                SELECT user_id, season_id, cherries, pass_tier, auto_claim_enabled, bonus_last_claim_date
                FROM ivent_pass_users
                WHERE user_id = %s AND season_id = %s
                LIMIT 1
            """, (uid, SEASON_ID))
        row = cursor.fetchone()

        if row:
            # 2. Возвращаем словарь с новыми полями
            return {
                "user_id": row[0],
                "season_id": row[1],
                "cherries": row[2],
                "pass_tier": row[3],
                "auto_claim_enabled": row[4],
                "bonus_last_claim_date": str(row[5]) if row[5] else None,
            }

        # 3. При создании нового пользователя устанавливаем pass_tier=0 и auto_claim_enabled=False
        cursor.execute("""
                INSERT INTO ivent_pass_users (user_id, season_id, cherries, pass_tier, auto_claim_enabled, bonus_last_claim_date)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING user_id, season_id, cherries, pass_tier, auto_claim_enabled, bonus_last_claim_date
            """, (uid, SEASON_ID, 0, 0, False, None))
        row = cursor.fetchone()
        conn.commit()

        # 4. Возвращаем новый словарь
        return {
            "user_id": row[0],
            "season_id": row[1],
            "cherries": row[2],
            "pass_tier": row[3],
            "auto_claim_enabled": row[4],
            "bonus_last_claim_date": str(row[5]) if row[5] else None,
        }
    finally:
        cursor.close()
        conn.close()


async def get_pass_user(user_id: int):
    """Без изменений"""
    return await get_or_create_pass_user(user_id)


async def update_pass_user(user_id: int, updates: dict):
    """Изменено: Добавлены новые поля в список разрешенных."""
    uid = str(user_id)

    # Добавляем 'pass_tier' и 'auto_claim_enabled', убираем 'is_ultra'
    allowed_fields = {
        "cherries",
        "pass_tier",
        "auto_claim_enabled",
        "bonus_last_claim_date",
    }

    set_parts = []
    values = []
    for key, value in updates.items():
        if key in allowed_fields:
            set_parts.append(f"{key} = %s")
            values.append(value)

    if not values:
        return False

    set_parts.append("updated_at = NOW()")
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


async def add_cherries(user_id: int, amount: int):
    """Без изменений на этом этапе"""
    user = await get_pass_user(user_id)
    new_cherries = int(user.get("cherries", 0)) + int(amount)
    await update_pass_user(user_id, {"cherries": new_cherries})
    return new_cherries


async def get_claimed_levels(user_id: int) -> dict:
    """Без изменений"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
      SELECT level, claimed_regular, claimed_ultra
      FROM ivent_pass_claims
      WHERE user_id = %s AND season_id = %s
    """, (user_id, SEASON_ID))
        rows = cursor.fetchall()
        claimed_data = {}
        for row in rows:
            claimed_data[str(row['level'])] = {
                "regular": row['claimed_regular'],
                "ultra": row['claimed_ultra']
            }
        return claimed_data
    finally:
        cursor.close()
        conn.close()


async def claim_level(user_id: int, level: int, regular: bool, ultra: bool):
    """Без изменений"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        set_parts = []
        if regular:
            set_parts.append("claimed_regular = TRUE")
        if ultra:
            set_parts.append("claimed_ultra = TRUE")
        if not set_parts:
            return
        set_query_part = ", ".join(set_parts)
        cursor.execute(f"""
      INSERT INTO ivent_pass_claims (user_id, season_id, level, claimed_regular, claimed_ultra)
      VALUES (%s, %s, %s, %s, %s)
      ON CONFLICT (user_id, season_id, level)
      DO UPDATE SET {set_query_part}
    """, (user_id, SEASON_ID, level, regular, ultra))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


async def get_today_tasks(user_id: int):
    """Без изменений"""
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
                "id": row[0], "task_id": row[1], "text": row[2], "progress": row[3],
                "target": row[4], "reward": row[5], "is_completed": row[6], "claimed": row[7],
            })
        return tasks
    finally:
        cursor.close()
        conn.close()


async def create_daily_tasks(user_id: int, tasks_count: int):
    """Изменено: Принимает количество заданий для создания."""
    uid = str(user_id)
    today = today_date()
    selected_tasks = random.sample(DAILY_TASK_POOL, tasks_count)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for task in selected_tasks:
            cursor.execute("""
                INSERT INTO ivent_pass_daily_tasks (user_id, season_id, task_date, task_id, task_text, progress, target, reward, is_completed, claimed)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (uid, SEASON_ID, today, task["id"], task["text"], 0, task["target"], task["reward"], False, False))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return await get_today_tasks(user_id)


async def get_or_create_today_tasks(user_id: int):
    """Изменено: Определяет, сколько заданий нужно создать, в зависимости от pass_tier."""
    tasks = await get_today_tasks(user_id)
    if tasks:
        return tasks

    # Получаем pass_tier пользователя
    user = await get_pass_user(user_id)
    pass_tier = user.get("pass_tier", 0)

    # Определяем, сколько заданий создать
    tasks_to_create = MEGA_PASS_TASKS_COUNT if pass_tier == PASS_TIER_MEGA else DAILY_TASKS_COUNT

    return await create_daily_tasks(user_id, tasks_to_create)


async def update_task_progress(task_row_id: int, progress: int, is_completed: bool):
    """Без изменений"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE ivent_pass_daily_tasks SET progress = %s, is_completed = %s WHERE id = %s
        """, (progress, is_completed, task_row_id))
        conn.commit()
        return True
    finally:
        cursor.close()
        conn.close()


async def claim_daily_bonus(user_id: int):
    """Изменено: Логика бонуса теперь зависит от pass_tier."""
    # Импортируем все нужные константы
    from .pass_data import DAILY_BONUS_REWARD, ULTRA_PASS_DAILY_BONUS, MEGA_PASS_DAILY_BONUS

    user = await get_pass_user(user_id)
    today = today_date()
    last_claim = user.get("bonus_last_claim_date")
    if last_claim == str(today):
        return False, 0, user.get("cherries", 0)

    # Новая логика расчета бонуса
    bonus_to_add = DAILY_BONUS_REWARD
    pass_tier = user.get("pass_tier", 0)
    if pass_tier == PASS_TIER_ULTRA:
        bonus_to_add += ULTRA_PASS_DAILY_BONUS
    elif pass_tier == PASS_TIER_MEGA:
        bonus_to_add += MEGA_PASS_DAILY_BONUS

    new_cherries = int(user.get("cherries", 0)) + bonus_to_add
    await update_pass_user(user_id, {
        "cherries": new_cherries,
        "bonus_last_claim_date": today
    })
    return True, bonus_to_add, new_cherries


async def has_claimed_daily_bonus(user_id: int):
    """Без изменений"""
    user = await get_pass_user(user_id)
    return user.get("bonus_last_claim_date") == str(today_date())


async def set_pass_tier(user_id: int, tier: int):
    """Новая функция вместо set_ultra_pass. Устанавливает уровень пропуска."""
    await update_pass_user(user_id, {"pass_tier": tier})
    return True