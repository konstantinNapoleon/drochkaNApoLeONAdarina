import time
import random
from aiogram import Router, types, F
from aiogram.filters import Command

router = Router()

FARMCOIN_EMOJI = "💰"
# Кулдаун 24 часа
BONUS_COOLDOWN_SEC = 24 * 60 * 60


def ensure_inv_dict(user) -> dict:
    """Гарантирует, что инвентарь — это словарь (защита от удаления данных)"""
    inv = user.get("inventory")
    if not isinstance(inv, dict):
        if isinstance(inv, list):
            new_inv = {}
            for item in inv:
                new_inv[item] = new_inv.get(item, 0) + 1
            user["inventory"] = new_inv
        else:
            user["inventory"] = {}
    return user["inventory"]


@router.message(Command("bonus", "daily", "ежедневный", "dailybonus"))
async def daily_bonus(message: types.Message, get_user, save_db):
    user = get_user(message.from_user.id, message.from_user.username)

    now = int(time.time())
    last = int(user.get("last_bonus_time", 0) or 0)

    time_passed = now - last
    if time_passed < BONUS_COOLDOWN_SEC:
        remaining = BONUS_COOLDOWN_SEC - time_passed
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        seconds = remaining % 60
        return await message.answer(
            f"⏳ Бонус уже получен.\n"
            f"Повтори через: <b>{hours:02d}:{minutes:02d}:{seconds:02d}</b>",
            parse_mode="HTML"
        )

    bonus_amount = random.randint(100, 500)

    # Получаем инвентарь-словарь
    inv = ensure_inv_dict(user)

    # Плюсуем монеты в инвентарь
    inv[FARMCOIN_EMOJI] = inv.get(FARMCOIN_EMOJI, 0) + bonus_amount
    user["last_bonus_time"] = now

    # --- SQLITE FIX: Передаем ID и объект пользователя ---
    save_db(message.from_user.id, user)

    await message.answer(
        f"🎁 Ежедневный бонус: <b>+{bonus_amount}</b> {FARMCOIN_EMOJI}\n"
        f"Теперь всего в инвентаре: <b>{inv[FARMCOIN_EMOJI]:,}</b>",
        parse_mode="HTML"
    )
