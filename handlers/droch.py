import time
import html
import random
from datetime import datetime, timezone, timedelta
from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from items import GAME_ITEMS
from handlers.etel import get_user_buffs

router = Router()
MSK_TZ = timezone(timedelta(hours=3))
FARMCOIN_EMOJI = "💰"

# --- КОНФИГИ НОВОВВЕДЕНИЙ ---
DROP_CHANCE = 0.05
DROP_ITEMS = ["🔑", "💦", "📕", "💜", "🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "🟪"]

RANKS = {
    1: "🙋 Школьник", 20: "🚬 Студент", 50: "🔫 Начинающий", 100: "👏 Прогрессирующий",
    200: "⭐️ Профессионал", 300: "🥇 Авторитет", 500: "🌟 Властелин дрочки", 750: "⭐️⭐️ Легенда",
    1000: "🌟🌟 Охотник за семенем", 3000: "⭐️⭐️⭐️ Генерал дрочки", 5000: "🌟🌟🌟 Бесконечный дрочер",
    10000: "🏆 Гранд-повелитель", 50000: "💎 Демиург Онанизма", 100000: "👑 Хранитель семени"
}


def get_current_rank(droch_count: int) -> str:
    current_rank = "👶 Новичок"
    for count in sorted(RANKS.keys()):
        if droch_count >= count:
            current_rank = RANKS[count]
        else:
            break
    return current_rank


def get_current_date_str(): return datetime.now(MSK_TZ).strftime("%Y-%m-%d")


def get_real_total(user) -> int:
    chats_data = user.get("chats_data", {})
    total_from_chats = sum(c.get("masturbations_count", 0) for c in chats_data.values())
    return max(user.get("total_droch_count", 0), total_from_chats)


def ensure_inv_dict(user) -> dict:
    inv = user.get("inventory")
    if not isinstance(inv, dict):
        if isinstance(inv, list):
            new_inv = {}
            for item in inv: new_inv[item] = new_inv.get(item, 0) + 1
            user["inventory"] = new_inv
        else:
            user["inventory"] = {}
    return user["inventory"]


def get_spray_markup(spray_count: int, user_id: int):
    if spray_count <= 0: return None
    builder = InlineKeyboardBuilder()
    builder.button(text=f"💦 Применить спрей ({spray_count})", callback_data=f"use_spray_callback:{user_id}")
    return builder.as_markup()


# --- СИСТЕМА СТРЕССА ---
async def update_stress(user):
    now = time.time()
    last_update = user.get("last_stress_update", now)
    elapsed = now - last_update
    if elapsed >= 15:
        decay = int(elapsed // 15)
        user["stress"] = max(0, user.get("stress", 0) - decay)
        user["last_stress_update"] = now - (elapsed % 15)
    else:
        user["last_stress_update"] = last_update
    return user


# --- ПРОФИЛЬ ---
def get_me_markup(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Закрыть", callback_data=f"inv_close_{user_id}")
    builder.adjust(1)
    return builder.as_markup()


def get_me_text(user, chat_id: str, full_name: str):
    chats_data = user.get("chats_data", {})
    inv = ensure_inv_dict(user)
    buffs = get_user_buffs(user)
    stamina_bonus = int((buffs["stamina_multiplier"] - 1.0) * 100)
    luck_bonus = int((buffs["luck_multiplier"] - 1.0) * 100)
    total_global = get_real_total(user)
    rank = get_current_rank(total_global)
    farmcoin_count = inv.get(FARMCOIN_EMOJI, 0)
    stress = user.get("stress", 0)
    total_in_groups = sum(c.get("masturbations_count", 0) for cid, c in chats_data.items() if int(cid) < 0)
    daily_droch = user.get("daily_stats", {}).get(get_current_date_str(), 0)
    chat_droch = chats_data.get(chat_id, {}).get("masturbations_count", 0)

    return (
        f"👤 <b>Профиль:</b> {html.escape(full_name)}\n"
        f"━━━━━━━━━━━━━━\n"
        f"🎖 <b>Позывной:</b> {rank}\n\n"
        f"{FARMCOIN_EMOJI} ФармКоин: <b>{farmcoin_count:,}</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"💪 <b>Характеристики:</b>\n"
        f"├ 🧤 Выносливость: <b>{stamina_bonus}%</b>\n"
        f"└ 🍀 Удача: <b>{luck_bonus}%</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"📊 <b>Статистика дрочки:</b>\n"
        f"├ 🧘 Стресс: <b>{stress}%</b>\n"
        f"├ 🎲 В этом чате: <b>{chat_droch}</b>\n"
        f"├ 🔥 За сегодня: <b>{daily_droch}</b> \n"
        f"└ 🏆 Всего в группах (ТОП): <b>{total_in_groups}</b> \n"
    )


@router.message(Command("me"))
async def cmd_me(message: types.Message, get_user):
    user = await get_user(message.from_user.id, message.from_user.username)
    text = get_me_text(user, str(message.chat.id), message.from_user.full_name)
    await message.reply(text, parse_mode="HTML", reply_markup=get_me_markup(message.from_user.id))


@router.callback_query(F.data.startswith("open_me:"))
async def callback_open_me(callback: types.CallbackQuery, get_user):
    owner_id = int(callback.data.split(":")[1])
    if callback.from_user.id != owner_id: return await callback.answer("Это не твой профиль!", show_alert=True)
    user = await get_user(callback.from_user.id, callback.from_user.username)
    text = get_me_text(user, str(callback.message.chat.id), callback.from_user.full_name)
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_me_markup(owner_id))
    except Exception:
        await callback.answer()


# --- ЛОГИКА ДРОЧКИ ---
async def process_droch(message: types.Message, get_user, save_db):
    user = await get_user(message.from_user.id, message.from_user.username)
    user = await update_stress(user)
    chat_id = str(message.chat.id)
    inv = ensure_inv_dict(user)
    current_time = time.time()

    if user.get("stress", 0) >= 100: return await message.reply(
        "Твой стресс слишком высок, поэтому твой дружок не встаёт")

    belt_expire = user.get("belt_expire_time", 0)
    if current_time < belt_expire:
        remaining = int(belt_expire - current_time)
        return await message.reply(f"На тебе пояс верности. 🔒 Ты не можешь дрочить ещё {remaining // 3600}ч.",
                                   parse_mode="HTML")

    buffs = get_user_buffs(user)
    current_cooldown = int(1800 / buffs["stamina_multiplier"])
    chat_stats = user.setdefault("chats_data", {}).setdefault(chat_id, {"masturbations_count": 0, "last_droch_time": 0,
                                                                        "chat_name": ""})
    chat_stats["chat_name"] = message.chat.title or "Личные сообщения"

    if (current_time - chat_stats.get("last_droch_time", 0)) < current_cooldown:
        return await message.reply("Ты недавно дрочил! 🤕",
                                   reply_markup=get_spray_markup(inv.get("💦", 0), message.from_user.id))

    chat_stats["masturbations_count"] += 1
    total_droch = get_real_total(user) + 1
    user["total_droch_count"] = total_droch
    user["stress"] = min(100, user.get("stress", 0) + 3)

    # --- НОВОВВЕДЕНИЯ ---
    extra_msg = ""
    achievements = user.setdefault("achievements", [])
    if "first_droch" not in achievements:
        achievements.append("first_droch")
        inv["💦"] = inv.get("💦", 0) + 20
        inv["📕"] = inv.get("📕", 0) + 5
        inv["🔑"] = inv.get("🔑", 0) + 10
        extra_msg = "\n\n🎁 <b>БОНУС ЗА ПЕРВУЮ ДРОЧКУ:</b>\n+20 💦, +5 📕, +10 🔑"
    elif random.random() < DROP_CHANCE:
        item = random.choice(DROP_ITEMS)
        qty = random.randint(2, 6)
        inv[item] = inv.get(item, 0) + qty
        info = GAME_ITEMS.get(item, {"name": item, "description": "Предмет"})
        extra_msg = f"\n\n✨ <b>Тебе выпал предмет:</b> {item} <b>{info.get('name', item)}</b> ({info.get('description', '')}) x{qty}"

    if "daily_stats" not in user: user["daily_stats"] = {}
    user["daily_stats"][get_current_date_str()] = user["daily_stats"].get(get_current_date_str(), 0) + 1

    chat_stats["last_droch_time"] = current_time
    await save_db(message.from_user.id, user)
    await message.reply(
        f"Ты успешно вздрочнул! 😼\nНа твоем счету <b>{chat_stats['masturbations_count']}</b> вздрочки.{extra_msg}",
        reply_markup=get_spray_markup(inv.get("💦", 0), message.from_user.id), parse_mode="HTML")


@router.callback_query(F.data.startswith("use_spray_callback:"))
async def callback_use_spray(callback: types.CallbackQuery, get_user, save_db):
    _, owner_id = callback.data.split(":")
    if callback.from_user.id != int(owner_id): return await callback.answer("Это не твой спрей!", show_alert=True)
    user = await get_user(callback.from_user.id, callback.from_user.username)
    inv = ensure_inv_dict(user)
    if inv.get("💦", 0) <= 0: return await callback.answer("У тебя нет спрея!")
    inv["💦"] -= 1
    user.setdefault("chats_data", {}).setdefault(str(callback.message.chat.id), {})["last_droch_time"] = 0
    await save_db(callback.from_user.id, user)
    await callback.message.edit_text("Ты применил спрей. 👍 Жми: /drochnut")


@router.message(Command("drochnut", "дрочнуть"))
async def cmd_drochnut(message: types.Message, get_user, save_db): await process_droch(message, get_user, save_db)


@router.message(F.text.lower().in_({"дрочнуть", "юз рука", "юз хуй"}))
async def text_drochnut(message: types.Message, get_user, save_db): await process_droch(message, get_user, save_db)


@router.message(F.text.lower() == "юз 💦")
async def use_spray_cmd(message: types.Message, get_user, save_db):
    user = await get_user(message.from_user.id, message.from_user.username)
    inv = ensure_inv_dict(user)
    if inv.get("💦", 0) <= 0: return await message.reply("У тебя нет Спрея!")
    user.setdefault("chats_data", {}).setdefault(str(message.chat.id), {})["last_droch_time"] = 0
    inv["💦"] -= 1
    await save_db(message.from_user.id, user)
    await message.reply("Ты применил <b>спрей</b>! 🌼 Жми: /drochnut", parse_mode="HTML")






