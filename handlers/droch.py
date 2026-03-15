import time
from datetime import datetime, timezone, timedelta
from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Импортируем расчет баффов
from handlers.etel import get_user_buffs

router = Router()

MSK_TZ = timezone(timedelta(hours=3))

RANKS = {
    1: "🙋 Школьник",
    20: "🚬 Студент",
    50: "🔫 Начинающий",
    100: "👏 Прогрессирующий",
    200: "⭐️ Профессионал",
    300: "🥇 Авторитет",
    500: "🌟 Властелин дрочки",
    750: "⭐️⭐️ Легенда",
    1000: "🌟🌟 Охотник за семенем",
    3000: "⭐️⭐️⭐️ Генерал дрочки",
    5000: "🌟🌟🌟 Бесконечный дрочер",
    10000: "🏆 Гранд-повелитель",
    50000: "💎 Демиург Онанизма",
    100000: "👑 Хранитель семени"
}


def get_current_rank(droch_count: int) -> str:
    \"\"\"Определяет ранг на основе общего количества дрочек.\"\"\"
    current_rank = "👶 Новичок"
    for count in sorted(RANKS.keys()):
        if droch_count >= count:
            current_rank = RANKS[count]
        else:
            break
    return current_rank


def get_current_date_str():
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
    inv = ensure_inv_dict(user)
    spray_count = inv.get("💦", 0)
    current_time = time.time()

    # --- ПРОВЕРКА ПОЯСА ВЕРНОСТИ ---
    belt_expire = user.get("belt_expire_time", 0)
    if current_time < belt_expire:
        remaining = int(belt_expire - current_time)
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        return await message.reply(
            f"На тебе пояс верности. 🔒 Ты не можешь дрочить ещё <b>{hours}ч. {minutes}мин.</b>!",
            parse_mode="HTML"
        )

    # --- РАСЧЕТ ДИНАМИЧЕСКОГО КД ---
    buffs = get_user_buffs(user)
    BASE_COOLDOWN = 1800  # 30 минут
    current_cooldown = int(BASE_COOLDOWN / buffs["stamina_multiplier"])

    if "chats_data" not in user:
        user["chats_data"] = {}
    if chat_id not in user["chats_data"]:
        user["chats_data"][chat_id] = {"masturbations_count": 0, "last_droch_time": 0, "chat_name": ""}

    chat_stats = user["chats_data"][chat_id]
    chat_stats["chat_name"] = message.chat.title or "Личные сообщения"

    last_time = chat_stats.get("last_droch_time", 0)
    time_passed = current_time - last_time

    # Проверяем КД
    if time_passed < current_cooldown:
        remaining_seconds = int(current_cooldown - time_passed)
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60

        buff_text = ""
        if buffs["stamina_multiplier"] > 1.0:
            percent = int((buffs["stamina_multiplier"] - 1.0) * 100)
            buff_text = f"\n<i>(Твое КД снижено на {percent}% благодаря баффам!)</i>"

        return await message.reply(
            f"Ты недавно дрочил! 🤕 \n"
            f"Приходи через <b>{minutes} мин. {seconds} сек.</b>{buff_text}",
            reply_markup=get_spray_markup(spray_count, message.from_user.id),
            parse_mode="HTML"
        )

    # Обновление статистики (в текущем чате)
    chat_stats["masturbations_count"] += 1

    # --- ОБНОВЛЕНИЕ РАНГА (Глобально) ---
    total_droch = user.get("total_droch_count", 0) + 1
    user["total_droch_count"] = total_droch

    # Если текущее число есть в словаре рангов — поздравляем
    if total_droch in RANKS:
        new_rank = RANKS[total_droch]
        await message.answer(f"🎉 Поздравляем! Твоё новое звание: <b>{new_rank}</b>!", parse_mode="HTML")

    # Обновляем строковое значение ранга в профиле
    user["rank"] = get_current_rank(total_droch)

    # --- ЛОГИКА ДОЗАТОРА СПРЕЯ ---
    dispenser_active = user.get("spray_dispenser_active", False)
    dispenser_triggered = False

    # Если дозатор включен, он есть в инвентаре и есть спреи
    if dispenser_active and inv.get("🚰", 0) > 0 and inv.get("💦", 0) > 0:
        inv["💦"] -= 1  # Тратим 1 спрей автоматически
        chat_stats["last_droch_time"] = 0  # СБРАСЫВАЕМ КД В НОЛЬ
        dispenser_triggered = True
    else:
        chat_stats["last_droch_time"] = current_time  # Обычное КД

    if "daily_stats" not in user:
        user["daily_stats"] = {}

    current_date = get_current_date_str()
    current_daily = user["daily_stats"].get(current_date, 0)
    user["daily_stats"][current_date] = current_daily + 1

    if "achievements" not in user or not isinstance(user["achievements"], list):
        user["achievements"] = []
    if "first_droch" not in user["achievements"]:
        user["achievements"].append("first_droch")
        await message.answer("🎊 НОВОЕ ДОСТИЖЕНИЕ: ✊ Первая дрочка!")

    await save_db(message.from_user.id, user)

    # --- ФОРМИРУЕМ ОТВЕТ ---
    if dispenser_triggered:
        reply_text = (
            f"Ты успешно вздрочнул! 😼\n"
            f"На твоем счету <b>{chat_stats['masturbations_count']}</b> вздрочки.\n\n"
            f"🚰 Дозатор спрея сработал и теперь можешь дрочить ещё раз!"
        )
        await message.reply(reply_text, parse_mode="HTML")
    else:
        reply_text = (
            f"Ты успешно вздрочнул! 😼\n"
            f"На твоем счету <b>{chat_stats['masturbations_count']}</b> вздрочки."
        )
        await message.reply(reply_text, reply_markup=get_spray_markup(inv.get("💦", 0), message.from_user.id),
                            parse_mode="HTML")


@router.callback_query(F.data.startswith("use_spray_callback:"))
async def callback_use_spray(callback: types.CallbackQuery, get_user, save_db):
    _, owner_id = callback.data.split(":")
    if callback.from_user.id != int(owner_id):
        return await callback.answer("Это не твой спрей!", show_alert=True)

    user = await get_user(callback.from_user.id, callback.from_user.username)
    current_time = time.time()

    if current_time < user.get("belt_expire_time", 0):
        return await callback.answer("Пояс верности мешает использовать спрей! 🔒", show_alert=True)

    chat_id = str(callback.message.chat.id)
    inv = ensure_inv_dict(user)
    buffs = get_user_buffs(user)
    current_cooldown = int(1800 / buffs["stamina_multiplier"])

    chat_stats = user.get("chats_data", {}).get(chat_id)
    if not chat_stats:
        return await callback.answer("Ошибка данных чата.")

    last_time = chat_stats.get("last_droch_time", 0)

    if (current_time - last_time) < current_cooldown:
        inv["💦"] -= 1
        chat_stats["last_droch_time"] = 0
        await save_db(callback.from_user.id, user)
        await callback.message.edit_text("Ты применил спрей. 👍 Жми: /drochnut")
    else:
        await callback.answer("Спрей тебе сейчас не нужен!")


@router.message(Command("drochnut", "дрочнуть"))
async def cmd_drochnut(message: types.Message, get_user, save_db):
    await process_droch(message, get_user, save_db)


@router.message(F.text.lower().in_({"дрочнуть", "юз рука", "юз хуй"}))
async def text_drochnut(message: types.Message, get_user, save_db):
    await process_droch(message, get_user, save_db)


@router.message(F.text.lower() == "юз 💦")
async def use_spray_cmd(message: types.Message, get_user, save_db):
    user = await get_user(message.from_user.id, message.from_user.username)
    current_time = time.time()

    if current_time < user.get("belt_expire_time", 0):
        return await message.reply("Пояс верности мешает использовать спрей! 🔒")

    chat_id = str(message.chat.id)
    inv = ensure_inv_dict(user)
    buffs = get_user_buffs(user)
    current_cooldown = int(1800 / buffs["stamina_multiplier"])

    if inv.get("💦", 0) <= 0:
        return await message.reply("У тебя нет Спрея!")

    chat_stats = user.get("chats_data", {}).get(chat_id, {"last_droch_time": 0})
    if (current_time - chat_stats["last_droch_time"]) < current_cooldown:
        inv["💦"] -= 1
        chat_stats["last_droch_time"] = 0
        await save_db(message.from_user.id, user)
        await message.reply("Ты применил <b>спрей</b>! 🌼 Жми: /drochnut", parse_mode="HTML")
    else:
        await message.reply("Спрей сейчас не нужен!")




