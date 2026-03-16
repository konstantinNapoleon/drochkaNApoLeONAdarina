import time
import html
from datetime import datetime, timezone, timedelta
from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Импортируем расчет баффов (убедись, что путь верный)
from handlers.etel import get_user_buffs

router = Router()

MSK_TZ = timezone(timedelta(hours=3))
FARMCOIN_EMOJI = "💠"

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
    current_rank = "👶 Новичок"
    for count in sorted(RANKS.keys()):
        if droch_count >= count:
            current_rank = RANKS[count]
        else:
            break
    return current_rank


def get_current_date_str():
    return datetime.now(MSK_TZ).strftime("%Y-%m-%d")


def get_real_total(user) -> int:
    """
    Суммирует все дрочки из всех чатов (chats_data).
    Это исправляет проблему 'Школьника' у старых игроков.
    """
    chats_data = user.get("chats_data", {})
    total_from_chats = sum(c.get("masturbations_count", 0) for c in chats_data.values())
    # Возвращаем максимум между сохраненным полем и реальной суммой из чатов
    return max(user.get("total_droch_count", 0), total_from_chats)


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

    # --- ПРОВЕРКА ПОЯСА ---
    belt_expire = user.get("belt_expire_time", 0)
    if current_time < belt_expire:
        remaining = int(belt_expire - current_time)
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        return await message.reply(
            f"На тебе пояс верности. 🔒 Ты не можешь дрочить ещё <b>{hours}ч. {minutes}мин.</b>!",
            parse_mode="HTML"
        )

    # --- КД ---
    buffs = get_user_buffs(user)
    BASE_COOLDOWN = 1800
    current_cooldown = int(BASE_COOLDOWN / buffs["stamina_multiplier"])

    if "chats_data" not in user:
        user["chats_data"] = {}
    if chat_id not in user["chats_data"]:
        user["chats_data"][chat_id] = {"masturbations_count": 0, "last_droch_time": 0, "chat_name": ""}

    chat_stats = user["chats_data"][chat_id]
    chat_stats["chat_name"] = message.chat.title or "Личные сообщения"

    last_time = chat_stats.get("last_droch_time", 0)
    time_passed = current_time - last_time

    if time_passed < current_cooldown:
        remaining_seconds = int(current_cooldown - time_passed)
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        return await message.reply(
            f"Ты недавно дрочил! 🤕 \nПриходи через <b>{minutes} мин. {seconds} сек.</b>",
            reply_markup=get_spray_markup(spray_count, message.from_user.id),
            parse_mode="HTML"
        )

    # --- ЛОГИКА СЧЕТЧИКОВ И РАНГА ---
    chat_stats["masturbations_count"] += 1

    # Исправляем и обновляем общий стаж
    total_droch = get_real_total(user) + 1
    user["total_droch_count"] = total_droch

    old_rank = user.get("rank", "👶 Новичок")
    current_calculated_rank = get_current_rank(total_droch)

    if current_calculated_rank != old_rank:
        user["rank"] = current_calculated_rank
        await message.answer(
            f"🎊 <b>Новое звание!</b>\n"
            f"Теперь ты: <b>{current_calculated_rank}</b>!",
            parse_mode="HTML"
        )

    # --- СПРЕИ ---
    dispenser_active = user.get("spray_dispenser_active", False)
    dispenser_triggered = False
    if dispenser_active and inv.get("🚰", 0) > 0 and inv.get("💦", 0) > 0:
        inv["💦"] -= 1
        chat_stats["last_droch_time"] = 0
        dispenser_triggered = True
    else:
        chat_stats["last_droch_time"] = current_time

    if "daily_stats" not in user:
        user["daily_stats"] = {}
    current_date = get_current_date_str()
    user["daily_stats"][current_date] = user["daily_stats"].get(current_date, 0) + 1

    await save_db(message.from_user.id, user)

    # Ответ
    res_text = f"Ты успешно вздрочнул! 😼\nНа твоем счету <b>{chat_stats['masturbations_count']}</b> вздрочки."
    if dispenser_triggered:
        res_text += "\n\n🚰 Дозатор спрея сработал!"

    await message.reply(res_text, parse_mode="HTML",
                        reply_markup=None if dispenser_triggered else get_spray_markup(inv.get("💦", 0),
                                                                                       message.from_user.id))


@router.message(Command("me"))
async def cmd_me(message: types.Message, get_user):
    user = await get_user(message.from_user.id, message.from_user.username)
    chat_id = str(message.chat.id)
    chats_data = user.get("chats_data", {})

    # Считаем реальный общий стаж (для ранга)
    total_global = get_real_total(user)
    rank = get_current_rank(total_global)

    # Считаем сумму ТОЛЬКО в группах (для синхронизации с /topdroch)
    total_in_groups = sum(
        c.get("masturbations_count", 0)
        for cid, c in chats_data.items()
        if int(cid) < 0
    )

    farmcoin_count = user.get("farm_coins", 0)
    balance = user.get("balance", 0)
    total_farmed = user.get("total_farm_coins", 0)

    current_date = get_current_date_str()
    daily_droch = user.get("daily_stats", {}).get(current_date, 0)
    chat_droch = chats_data.get(chat_id, {}).get("masturbations_count", 0)

    text = (
        f"👤 <b>Профиль:</b> {html.escape(message.from_user.full_name)}\n"
        f"━━━━━━━━━━━━━━\n"
        f"🎖 <b>Звание:</b> {rank}\n\n"
        f"{FARMCOIN_EMOJI} ФармКоин: <b>{farmcoin_count:,}</b>\n"
        f"💰 Баланс: <b>{balance:,}</b> 🪙\n"
        f"📈 Всего нафармлено: <b>{total_farmed:,}</b> 🪙\n"
        f"━━━━━━━━━━━━━━\n"
        f"📊 <b>Статистика дрочки:</b>\n"
        f"├ В этом чате: <code>{chat_droch}</code>\n"
        f"├ За сегодня: <b>{daily_droch}</b> 🔥\n"
        f"├ Всего в группах (ТОП): <b>{total_in_groups}</b> 🏆\n"
        f"└ Общий стаж (РАНГ): <b>{total_global}</b>"
    )

    await message.reply(text, parse_mode="HTML")


# --- КОМАНДЫ ДРОЧКИ ---
@router.message(Command("drochnut", "дрочнуть"))
async def cmd_drochnut(message: types.Message, get_user, save_db):
    await process_droch(message, get_user, save_db)


@router.message(F.text.lower().in_({"дрочнуть", "юз рука", "юз хуй"}))
async def text_drochnut(message: types.Message, get_user, save_db):
    await process_droch(message, get_user, save_db)


@router.callback_query(F.data.startswith("use_spray_callback:"))
async def callback_use_spray(callback: types.CallbackQuery, get_user, save_db):
    _, owner_id = callback.data.split(":")
    if callback.from_user.id != int(owner_id):
        return await callback.answer("Это не твой спрей!", show_alert=True)
    user = await get_user(callback.from_user.id, callback.from_user.username)
    chat_id = str(callback.message.chat.id)
    inv = ensure_inv_dict(user)
    chat_stats = user.get("chats_data", {}).get(chat_id)
    if chat_stats:
        inv["💦"] -= 1
        chat_stats["last_droch_time"] = 0
        await save_db(callback.from_user.id, user)
        await callback.message.edit_text("Спрей использован! Можно дрочить.")
    else:
        await callback.answer("Ошибка данных.")





