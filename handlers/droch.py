import html
import time
from aiogram import Router, types, F
from aiogram.filters import Command

router = Router()


# Вспомогательная функция (на случай, если ее нет в этом файле)
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


async def process_droch(message: types.Message, get_user, save_db):
    user = get_user(message.from_user.id, message.from_user.username)
    chat_id = str(message.chat.id)

    if "chats_data" not in user:
        user["chats_data"] = {}

    if chat_id not in user["chats_data"]:
        user["chats_data"][chat_id] = {
            "masturbations_count": 0,
            "last_droch_time": 0
        }

    chat_stats = user["chats_data"][chat_id]
    COOLDOWN = 1800
    current_time = time.time()
    last_time = chat_stats.get("last_droch_time", 0)
    time_passed = current_time - last_time

    if time_passed < COOLDOWN:
        remaining_seconds = int(COOLDOWN - time_passed)
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        return await message.reply(
            f"Ты недавно дрочил! 🤕 \n"
            f"Приходи через <b>{minutes} мин. {seconds} сек.</b>",
            parse_mode="HTML"
        )

    chat_stats["masturbations_count"] += 1
    chat_stats["last_droch_time"] = current_time

    # ИСПРАВЛЕННОЕ СОХРАНЕНИЕ ДЛЯ SQLITE (без наград)
    save_db(message.from_user.id, user)

    await message.reply(
        f"Ты успешно вздрочнул! 😼\n"
        f"На твоем счету <b>{chat_stats['masturbations_count']}</b> вздрочки.",
        parse_mode="HTML"
    )


@router.message(Command("drochnut", "дрочнуть"))
async def cmd_drochnut(message: types.Message, get_user, save_db):
    await process_droch(message, get_user, save_db)


@router.message(F.text.lower().in_({"дрочнуть", "юз рука", "юз хуй"}))
async def text_drochnut(message: types.Message, get_user, save_db):
    await process_droch(message, get_user, save_db)


# --- ИСПРАВЛЕННЫЙ ХЕНДЛЕР ЮЗ 💦 ---

@router.message(F.text.lower() == "юз 💦")
async def use_spray(message: types.Message, get_user, save_db):
    user = get_user(message.from_user.id, message.from_user.username)
    chat_id = str(message.chat.id)

    inv = ensure_inv_dict(user)
    spray_count = inv.get("💦", 0)

    if spray_count <= 0:
        return await message.reply("У тебя нет Спрея для хуя! Купи его в магазине. 🛒")

    if "chats_data" not in user:
        user["chats_data"] = {}
    if chat_id not in user["chats_data"]:
        user["chats_data"][chat_id] = {"masturbations_count": 0, "last_droch_time": 0}

    chat_stats = user["chats_data"][chat_id]
    COOLDOWN = 1800
    current_time = time.time()
    last_time = chat_stats.get("last_droch_time", 0)

    if (current_time - last_time) < COOLDOWN:
        inv["💦"] = spray_count - 1
        chat_stats["last_droch_time"] = 0

        # ИСПРАВЛЕННОЕ СОХРАНЕНИЕ ДЛЯ SQLITE
        save_db(message.from_user.id, user)

        await message.reply(
            "Ты применил <b>спрей для хуя</b> и можешь подрочить ещё раз! 🌼",
            parse_mode="HTML"
        )
    else:
        await message.reply(
            "Спрей для хуя тебе сейчас ничем не поможет, ты и так можешь дрочить! 😝",
            parse_mode="HTML"
        )
