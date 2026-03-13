import time
from aiogram import Router, F, types
from aiogram.filters import Command

router = Router()

import time

# Твой основной словарь предметов
GAME_ITEMS = {
    # ... твои предметы ...

}

# --- ОБНОВЛЕННАЯ СИСТЕМА БАФФОВ ---
BUFF_CONFIG = {
    "passive": {
        "🧤": {"stamina": 0.12},
        "👓": {"stamina": 0.10},
        "🧴": {"stamina": 0.13},
        "🥼": {"stamina": 0.15},
        "😷": {"stamina": -0.01},
        "🎱": {"luck": 0.05},
        "🎩": {"luck": 0.05},
        "🧿": {"luck": 0.07},
        "📓": {"luck": 0.20},
        "⚠️": {"luck": 0.01},
        "🧬": {"stamina": 0.05},
        "🎞": {"luck": 0.01},
        "🏚": {"stamina": 0.02, "luck": -0.01},
        "🏠": {"stamina": 0.03},
        "🏰": {"stamina": 0.05},
        "🎄": {"luck": 0.02, "stamina": 0.05},
        "💐": {"luck": 0.05, "stamina": 0.05},
        "🧨": {"luck": 0.01}
    },
    "active": {
        "🚬": {"stamina": 0.10, "duration": 43200}, # 12 часов = 43200 сек
        "⛄️": {"luck": 0.05, "duration": 86400},  # 24 часа = 86400 сек
        "🦠": {"stamina": -0.30, "duration": 432000} # 5 дней = 432000 сек
    }
}


def get_user_buffs(user):
    inv = user.get("inventory", {})
    if not isinstance(inv, dict): inv = {}

    total_stamina_bonus = 0.0
    total_luck_bonus = 0.0

    # 1. Считаем пассивные бонусы
    for emoji, bonuses in BUFF_CONFIG["passive"].items():
        if inv.get(emoji, 0) > 0:
            # Прибавляем выносливость, если она прописана для этого предмета
            total_stamina_bonus += bonuses.get("stamina", 0)
            # Прибавляем удачу, если она прописана
            total_luck_bonus += bonuses.get("luck", 0)

    # 2. Считаем активные (временные) бонусы
    active_effects = user.get("active_effects", {})
    current_time = time.time()
    for emoji, expire_time in list(active_effects.items()):
        if current_time < expire_time:
            config = BUFF_CONFIG["active"].get(emoji)
            if config:
                total_stamina_bonus += config.get("stamina", 0)
                total_luck_bonus += config.get("luck", 0)
        else:
            active_effects.pop(emoji, None)

    return {
        "stamina_multiplier": 1.0 + total_stamina_bonus,
        "luck_multiplier": 1.0 + total_luck_bonus
    }
