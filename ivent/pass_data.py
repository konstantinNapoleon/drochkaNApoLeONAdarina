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

PASS_LEVELS = {
    1: {"rewards": {"💰": 20000}},
    2: {"rewards": {"🚚": 1}},
    3: {"rewards": {"🍃": 2026}},
    4: {"rewards": {"💰": 32000}},
    5: {"rewards": {"💰": 10000, "📓": 1, "🎁": 1}},
    6: {"rewards": {"🔑": 50000}},
    7: {"rewards": {"💎": 10}},
    8: {"rewards": {"🎁": 2, "🔰": 1}},
    9: {"rewards": {"💰": 100000, "💐": 1}},
    10: {"rewards": {"🍌": 1}},
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
        "text": "Передать 1 вещь через /give",
        "target": 1,
        "reward": 20,
    },
    {
        "id": "dice_1",
        "text": "Сыграть в /dice 1 раз",
        "target": 1,
        "reward": 10,
    },
    {
        "id": "start_pm_1",
        "text": "Написать боту в ЛС через /start",
        "target": 1,
        "reward": 50,
    },
]

DAILY_BONUS_REWARD = 50
DAILY_TASKS_COUNT = 3

PASS_IMAGE_URL = None  # потом вставим сюда file_id или url фото
