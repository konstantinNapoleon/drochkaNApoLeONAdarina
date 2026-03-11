from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder  # Добавлено

router = Router()

import time
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timezone, timedelta

router = Router()

# Часовой пояс МСК (UTC+3), чтобы день сбрасывался правильно по московскому времени
MSK_TZ = timezone(timedelta(hours=3))


def get_current_date_str():
    """Возвращает текущую дату в формате YYYY-MM-DD по МСК"""
    return datetime.now(MSK_TZ).strftime("%Y-%m-%d")


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


# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ КНОПКИ ---
def get_spray_markup(spray_count: int, user_id: int):
    if spray_count <= 0:
        return None
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"💦 Применить спрей ({spray_count})",
        callback_data=f"use_spray_callback:{user_id}"
    )
    return builder.as_markup()


async def process_droch(message: types.Message, get_user, save_db):
    user = await get_user(message.from_user.id, message.from_user.username)
    chat_id = str(message.chat.id)

    # Считаем количество спреев для кнопки
    inv = ensure_inv_dict(user)
    spray_count = inv.get("💦", 0)

    if "chats_data" not in user:
        user["chats_data"] = {}
    if chat_id not in user["chats_data"]:
        user["chats_data"][chat_id] = {"masturbations_count": 0, "last_droch_time": 0, "chat_name": ""}

    chat_stats = user["chats_data"][chat_id]
    chat_stats["chat_name"] = message.chat.title or "Личные сообщения"

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
            reply_markup=get_spray_markup(spray_count, message.from_user.id),
            parse_mode="HTML"
        )

    # --- ОБНОВЛЕНИЕ СТАТИСТИКИ ЗА ВСЕ ВРЕМЯ ---
    chat_stats["masturbations_count"] += 1
    chat_stats["last_droch_time"] = current_time

    # --- ОБНОВЛЕНИЕ СТАТИСТИКИ ЗА СЕГОДНЯ ---
    if "daily_stats" not in user:
        user["daily_stats"] = {}

    current_date = get_current_date_str()
    current_daily = user["daily_stats"].get(current_date, 0)
    user["daily_stats"][current_date] = current_daily + 1
    # ----------------------------------------

    if "achievements" not in user or not isinstance(user["achievements"], list):
        user["achievements"] = []
    if "first_droch" not in user["achievements"]:
        user["achievements"].append("first_droch")
        await message.answer("🎊 НОВОЕ ДОСТИЖЕНИЕ: ✊ Первая дрочка!\n└ Вы сделали это в первый раз!")

    await save_db(message.from_user.id, user)

    await message.reply(
        f"Ты успешно вздрочнул! 😼\n"
        f"На твоем счету <b>{chat_stats['masturbations_count']}</b> вздрочки.",
        reply_markup=get_spray_markup(spray_count, message.from_user.id),
        parse_mode="HTML"
    )


# --- ОБРАБОТЧИК НАЖАТИЯ НА КНОПКУ СПРЕЯ ---
@router.callback_query(F.data.startswith("use_spray_callback:"))
async def callback_use_spray(callback: types.CallbackQuery, get_user, save_db):
    _, owner_id = callback.data.split(":")

    if callback.from_user.id != int(owner_id):
        return await callback.answer("Это не твой спрей!", show_alert=True)

    user = await get_user(callback.from_user.id, callback.from_user.username)
    chat_id = str(callback.message.chat.id)
    inv = ensure_inv_dict(user)
    spray_count = inv.get("💦", 0)

    if spray_count <= 0:
        return await callback.answer("У тебя нет Спреев для хуя!", show_alert=True)

    chat_stats = user.get("chats_data", {}).get(chat_id)
    if not chat_stats:
        return await callback.answer("Ошибка данных.")

    COOLDOWN = 1800
    current_time = time.time()
    last_time = chat_stats.get("last_droch_time", 0)

    if (current_time - last_time) < COOLDOWN:
        inv["💦"] = spray_count - 1
        chat_stats["last_droch_time"] = 0
        await save_db(callback.from_user.id, user)

        await callback.message.edit_text(
            "Ты применил спрей для хуя. 👍 Жми: /drochnut",
            reply_markup=None
        )
    else:
        await callback.answer("Спрей тебе сейчас не нужен!", show_alert=True)


@router.message(Command("drochnut", "дрочнуть"))
async def cmd_drochnut(message: types.Message, get_user, save_db):
    await process_droch(message, get_user, save_db)


@router.message(F.text.lower().in_({"дрочнуть", "юз рука", "юз хуй"}))
async def text_drochnut(message: types.Message, get_user, save_db):
    await process_droch(message, get_user, save_db)


@router.message(F.text.lower() == "юз 💦")
async def use_spray(message: types.Message, get_user, save_db):
    user = await get_user(message.from_user.id, message.from_user.username)
    chat_id = str(message.chat.id)
    inv = ensure_inv_dict(user)
    spray_count = inv.get("💦", 0)

    if spray_count <= 0:
        return await message.reply("У тебя нет Спрея для хуя! Купи его в магазине. 🛒")

    chat_stats = user.get("chats_data", {}).get(chat_id, {"last_droch_time": 0})
    if (time.time() - chat_stats["last_droch_time"]) < 1800:
        inv["💦"] = spray_count - 1
        chat_stats["last_droch_time"] = 0
        await save_db(message.from_user.id, user)
        await message.reply("Ты применил <b>спрей для хуя</b> и можешь подрочить ещё раз! 🌼 Жми: /drochnut",
                            parse_mode="HTML")
    else:
        await message.reply("Спрей для хуя тебе сейчас ничем не поможет! 😝", parse_mode="HTML")