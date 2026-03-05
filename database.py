import aiosqlite

DB_PATH = "bot_database.db"

# Создание таблицы при запуске бота
async def init_db():
  async with aiosqlite.connect(DB_PATH) as db:
    await db.execute("""
      CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance INTEGER DEFAULT 0
      )
    """)
    await db.commit()

# Обновление данных игрока (вызывай при каждом сообщении или действии)
async def update_user(user_id, username, score_to_add=0):
  async with aiosqlite.connect(DB_PATH) as db:
    await db.execute("""
      INSERT INTO users (user_id, username, balance) 
      VALUES (?, ?, ?)
      ON CONFLICT(user_id) DO UPDATE SET 
        username = excluded.username,
        balance = balance + ?
    """, (user_id, username, score_to_add, score_to_add))
    await db.commit()

# Получение Топ-10 игроков
async def get_top_players():
  async with aiosqlite.connect(DB_PATH) as db:
    async with db.execute("SELECT username, balance FROM users ORDER BY balance DESC LIMIT 10") as cursor:
      return await cursor.fetchall()