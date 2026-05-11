import datetime

# --- ОБЩИЕ НАСТРОЙКИ (Сохранены твои значения) ---
SEASON_ID = "s2_sects"
SEASON_TITLE = "ДРОЧ ПАСС | ВИШНЕВЫЙ ПАРАДОКС"
SEASON_DESCRIPTION = "Новый сезон с разделением на секты. Докажи, что ты можешь пройти их все."
SEASON_END = datetime.datetime.now() + datetime.timedelta(days=30)

# --- УРОВНИ ПРОПУСКА (TIERS) - НОВОЕ ---
# Вместо true/false теперь используем числа для гибкости
PASS_TIER_NORMAL = 0
PASS_TIER_ULTRA = 1
PASS_TIER_MEGA = 2

# --- ВАЛЮТА И ПРОГРЕСС (Обновлено) ---
CHERRY_EMOJI = "🍒"
CHERRIES_PER_LEVEL = 175
MAX_LEVEL = 50  # Увеличено с 40 до 50

# --- СТОИМОСТЬ ПРОПУСКОВ (Обновлено) ---
ULTRA_PASS_COST = 500  # Твоя текущая стоимость
MEGA_PASS_COST = 1350 # Новая стоимость Мега пропуска
MEGA_UPGRADE_COST = MEGA_PASS_COST - ULTRA_PASS_COST # Цена улучшения с Ультра до Мега

# --- ЕЖЕДНЕВНЫЙ БОНУС (Обновлено) ---
DAILY_BONUS_REWARD = 100
ULTRA_PASS_DAILY_BONUS = 150 # Твое значение
MEGA_PASS_DAILY_BONUS = 200   # Новое значение для Мега

# --- КОЛИЧЕСТВО ЗАДАНИЙ (Обновлено) ---
DAILY_TASKS_COUNT = 3
# Для Мега-пропуска будет 4 задания
MEGA_PASS_TASKS_COUNT = 4

# --- СТРУКТУРА СЕКТОРОВ (Добавлен новый сектор) ---
SECTORS = {
  'D': {'name': 'Новичок', 'levels': range(1, 11), 'unlocks_at': 0},
  'C': {'name': 'Начинающий', 'levels': range(11, 21), 'unlocks_at': 10},
  'B': {'name': 'Продвинутый', 'levels': range(21, 31), 'unlocks_at': 20},
  'A': {'name': 'Легенда', 'levels': range(31, 41), 'unlocks_at': 30},
  # НОВЫЙ СЕКТОР для Мега-пропуска
  'Бонус': {'name': 'Бонусный', 'levels': range(41, 51), 'unlocks_at': 40},
}

# --- ОБМЕН ВАЛЮТЫ (НОВОЕ) ---
# Курс обмена для Мега-игроков после 50-го уровня
CHERRY_TO_FRAG_RATE = 5

# --- НАГРАДЫ ЗА УРОВНИ (Твои награды 1-40 сохранены, добавлены 41-50) ---
PASS_LEVELS = {
  # --- ТВОИ НАГРАДЫ 1-40 ---
  1: {"rewards": {"💦": 120}, "ultra_rewards": {"💰": 2500}},
  2: {"rewards": {"🧱": 10}, "ultra_rewards": {"🪖": 5}},
  3: {"rewards": {"🔑": 2026}, "ultra_rewards": {"💦": 2026}},
  4: {"rewards": {"💰": 1000}, "ultra_rewards": {"🪙": 50}},
  5: {"rewards": {"💜": 111}, "ultra_rewards": {"🟡": 222}},
  6: {"rewards": {"💰": 4000}, "ultra_rewards": {"💰": 10000}},
  7: {"rewards": {"🧪": 1}, "ultra_rewards": {"🔑": 300}},
  8: {"rewards": {"📓": 1, "🍺": 250}, "ultra_rewards": {"🎞": 1}},
  9: {"rewards": {"💰": 2500}, "ultra_rewards": {"🪙": 20}},
  10: {"rewards": {"💰": 15000, "🎁": 2}, "ultra_rewards": {"🧬": 1, "🪙": 100, "🎁": 8}},

  11: {"rewards": {"🍺": 300}, "ultra_rewards": {"🎂": 5}},
  12: {"rewards": {"🚚": 1}, "ultra_rewards": {"🚛": 1}},
  13: {"rewards": {"🪙": 75}, "ultra_rewards": {"🪙": 125}},
  14: {"rewards": {"💦": 450}, "ultra_rewards": {"🔑": 750}},
  15: {"rewards": {"🍹": 1}, "ultra_rewards": {"🏴‍☠️": 1}},
  16: {"rewards": {"💰": 12000}, "ultra_rewards": {"💰": 25000}},
  17: {"rewards": {"🪙": 30}, "ultra_rewards": {"🧱": 20}},
  18: {"rewards": {"📓": 1, "🍺": 250}, "ultra_rewards": {"🎞": 1}},
  19: {"rewards": {"💎": 5}, "ultra_rewards": {"💰": 40000}},
  20: {"rewards": {"🔰": 1, "🎁": 5}, "ultra_rewards": {"🛡": 1, "🎁": 10}},

  21: {"rewards": {"💦": 1500}, "ultra_rewards": {"💦": 4500}},
  22: {"rewards": {"🇦🇱": 1}, "ultra_rewards": {"🏳️‍⚧️": 1}},
  23: {"rewards": {"🪙": 150}, "ultra_rewards": {"👙": 1}},
  24: {"rewards": {"💉": 400}, "ultra_rewards": {"🛌": 1000}},
  25: {"rewards": {"🧫": 1}, "ultra_rewards": {"📕": 350}},
  26: {"rewards": {"💰": 17500}, "ultra_rewards": {"🔍": 5}},
  27: {"rewards": {"💦": 1}, "ultra_rewards": {"🧱": 1}},
  28: {"rewards": {"🧱": 50}, "ultra_rewards": {"🪙": 500}},
  29: {"rewards": {"💰": 20000}, "ultra_rewards": {"👛": 1}},
  30: {"rewards": {"🧸": 1, "🎁": 5}, "ultra_rewards": {"💰": 350000, "🎁": 7}},

  31: {"rewards": {"🐔": 1}, "ultra_rewards": {"🦄": 1}},
  32: {"rewards": {"💐": 1, "💰": 15000}, "ultra_rewards": {"🏳️‍⚧️": 1}},
  33: {"rewards": {"💰": 20000, "🪙": 350, "🪖": 100}, "ultra_rewards": {"🖼": 1}},
  34: {"rewards": {"💦": 3000}, "ultra_rewards": {"🟠": 1000}},
  35: {"rewards": {"🇷🇺": 100}, "ultra_rewards": {"🇺🇦": 100}},
  36: {"rewards": {"🏀": 1}, "ultra_rewards": {"🏆": 1}},
  37: {"rewards": {"🎂": 35}, "ultra_rewards": {"🍬": 500}},
  38: {"rewards": {"🦠": 1, "💰": 100, "🔑": 200}, "ultra_rewards": {"🪙": 1000}},
  39: {"rewards": {"💜": 200}, "ultra_rewards": {"🎞": 10}},
  40: {"rewards": {"🍒": 1, "🎁": 20}, "ultra_rewards": {"🎁": 10}},

  # --- НОВЫЕ НАГРАДЫ ДЛЯ МЕГА-ПРОПУСКА (41-50) ---
  # Эти уровни будут доступны только с Мега пропуском.
  # Для простоты помещаем награды в 'rewards', логика доступа будет в коде.
  41: {"rewards": {"💰": 20000}},
  42: {"rewards": {"🧱": 250}},
  43: {"rewards": {"💎": 20}},
  44: {"rewards": {"🧴": 5}},
  45: {"rewards": {"🪖": 50}},
  46: {"rewards": {"🧨": 1}},
  47: {"rewards": {"🧸": 1}},
  48: {"rewards": {"🎁": 30}},
  49: {"rewards": {"💰": 10000}},
  50: {"rewards": {"💰": 500000}},
}

# --- ЕЖЕДНЕВНЫЕ ЗАДАНИЯ (Сохранены твои) ---
DAILY_TASK_POOL = [
  {"id": "chat_10", "text": "Написать 10 сообщений в чат", "target": 10, "reward": 50},
  {"id": "mast_20", "text": "Подрочить 20 раз", "target": 20, "reward": 100},
  {"id": "trade_1", "text": "Совершить 1 трейд", "target": 1, "reward": 40},
  {"id": "give_1", "text": "Передать вещь через /give", "target": 1, "reward": 20},
  {"id": "dice_1", "text": "Сыграть в /dice", "target": 1, "reward": 25},
  {"id": "ttt_1", "text": "Сыграть в крестики-нолики", "target": 1, "reward": 55},
  {"id": "shop_buy_1000", "text": "Купить вещь дороже 1000💰", "target": 1, "reward": 150},
]