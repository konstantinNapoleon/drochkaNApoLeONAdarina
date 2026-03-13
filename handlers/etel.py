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
        "🧤": {"stamina": 0.02},
        "🥼": {"stamina": 0.15},
        "🧴": {"stamina": 0.12},  # +1% выносливости
        "🧿": {"luck": 0.05},  # +5% удачи
        "🎩": {"luck": 0.02},  # +2% удачи
        "📚": {"stamina": 0.05, "luck": 0.05}  # СРАЗУ ОБА БОНУСА по +5%
    },
    "active": {
        "🚬": {"stamina": 0.10, "duration": 600}  # +10% выносливости на 10 мин
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
