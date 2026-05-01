import datetime

SEASON_ID = "banana_s1"
SEASON_TITLE = "ДРОЧ ПАСС | СЕЗОН 1: БАНАНОВЫЙ ПЕРЕПОЛОХ 🍌"
SEASON_DESCRIPTION = (
    "Время вкалывать. Каждый уровень — это не просто цифра, "
    "это твое превосходство. Забирай награды, пока другие спят."
)

PEACH_EMOJI = "🍑"
PEACHES_PER_LEVEL = 150
MAX_LEVEL = 10

# Укажи точную дату конца сезона при желании
SEASON_END = datetime.datetime(2026, 5, 11, 23, 59, 59)

# --- Настройки Ультра пропуска ---
ULTRA_PASS_COST = 500 # 500 Фрагов (🪙)
ULTRA_PASS_DAILY_BONUS = 25 # Дополнительные персики каждый день

PASS_LEVELS = {
  # Для каждого уровня теперь есть два поля:
  # "rewards" - для всех игроков
  # "ultra_rewards" - только для владельцев Ультра пропуска
  1: {
    "rewards": {"💰": 20000},
    "ultra_rewards": {"🪙": 10}
  },
  2: {
    "rewards": {"🚚": 1},
    "ultra_rewards": {"💰": 50000}
  },
  3: {
    "rewards": {"🍃": 2026},
    "ultra_rewards": {"🎁": 1}
  },
  4: {
    "rewards": {"💰": 32000},
    "ultra_rewards": {"🪙": 25}
  },
  5: {
    "rewards": {"💰": 10000, "📓": 1, "🎁": 1},
    "ultra_rewards": {"💰": 100000}
  },
  6: {
    "rewards": {"🔑": 1}, # Было 50000, предполагаю, что это была опечатка и имелась в виду цена, а не кол-во
    "ultra_rewards": {"🪙": 50}
  },
  7: {
    "rewards": {"💎": 1}, # Было 10, вероятно, тоже опечатка
    "ultra_rewards": {"🎁": 3}
  },
  8: {
    "rewards": {"🎁": 2, "🔰": 1},
    "ultra_rewards": {"💰": 250000}
  },
  9: {
    "rewards": {"💰": 100000, "💐": 1},
    "ultra_rewards": {"🪙": 100}
  },
  10: {
    "rewards": {"🍌": 1},
    "ultra_rewards": {"👑": 1, "💰": 500000},
    "achievement": "banana_legend"
  }
}

DAILY_TASK_POOL = [
    {
        "id": "chat_50",
        "text": "Написать в чат 50 сообщений",
        "target": 50,
        "reward": 200,
    },
    {
        "id": "mast_250",
        "text": "Подрочить 250 раз",
        "target": 250,
        "reward": 60,
    },
    {
        "id": "trade_1",
        "text": "Совершить 1 трейд",
        "target": 1,
        "reward": 40,
    },
    {
        "id": "give_1",
        "text": "Передать 5 вещей через /give",
        "target": 5,
        "reward": 20,
    },
    {
        "id": "dice_1",
        "text": "Сыграть в /dice 3 разф",
        "target": 3,
        "reward": 10,
    },
]

DAILY_BONUS_REWARD = 50
DAILY_TASKS_COUNT = 3

PASS_IMAGE_URL = None  # потом вставим сюда file_id или url фото
