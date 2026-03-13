import random
import time
from aiogram import Router, F, types
from aiogram.filters import Command

from items import GAME_ITEMS

router = Router()

FARMCOIN_EMOJI = "💰"
CASE_DROP_POOL = ["💦", "🍺", "🍬", "🚬", "💉"]
COOLDOWN_SECONDS = 86400  # КД для теста


def ensure_inv_dict(user) -> dict:
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


@router.message(Command("case"))
@router.message(F.text.lower() == "кейс")
async def open_case(message: types.Message, get_user, save_db):
    user_id = message.from_user.id
    user = await get_user(user_id, message.from_user.username)

    # Система КД (5 секунд)
    current_time = time.time()
    last_open = user.get("last_case_time", 0)

    if current_time - last_open < COOLDOWN_SECONDS:
        return await message.reply("Ты уже открывал кейс сегодня! 😔 Приходи завтра.")

    inv = ensure_inv_dict(user)

    # --- ЛОГИКА ВЫБОРА: ПРЕДМЕТ ИЛИ КОИНЫ ---
    reward_type = random.choice(["item", "coins"])

    if reward_type == "item":
        # Выпал предмет
        chosen_key = random.choice(CASE_DROP_POOL)
        item_info = GAME_ITEMS.get(chosen_key)
        count = random.randint(1, 8)

        inv[chosen_key] = inv.get(chosen_key, 0) + count
        response = f"Ты получил предмет {count} {chosen_key} {item_info['name']}: {item_info['description']}"

    else:
        # Выпали коины
        count = random.randint(50, 200)
        inv[FARMCOIN_EMOJI] = inv.get(FARMCOIN_EMOJI, 0) + count
        response = f"Ты получил предмет {count} {FARMCOIN_EMOJI} Фармкоины: Валюта для покупок"

    # Сохраняем данные
    user["last_case_time"] = current_time
    await save_db(user_id, user)

    await message.reply(response)
