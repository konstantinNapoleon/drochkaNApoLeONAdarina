from aiogram import Router, F, types
from aiogram.filters import Command

router = Router()


import random

def get_random_event():
    """
    Возвращает случайное событие с шансом 5%.
    Каждое событие имеет уникальный 'id' для разделения сообщений в основном коде.
    """
    if random.random() < 0.02:  # 5% шанс на выпадение события
        events = [
            {
                "id": "mom",
                "text": "😱 <b>Тебя спалила мамка!</b>\nОт стыда и страха ты не сможешь дрочить 2 часа.",
                "seconds": 7200  # 2 часа в секундах
            },
            {
                "id": "erection",
                "text": "🥀 <b>Хер не встал...</b>\nТвой дружок объявил забастовку. Ты не сможешь дрочить 2 часа 30 минут.",
                "seconds": 9000  # 2.5 часа в секундах
            }
        ]
        return random.choice(events)
    return None