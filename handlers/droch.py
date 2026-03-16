import time
import html
from datetime import datetime, timezone, timedelta
from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Импортируем расчет баффов
from handlers.etel import get_user_buffs

router = Router()

MSK_TZ = timezone(timedelta(hours=3))
FARMCOIN_EMOJI = "💰"

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
    chats_data = user.get("chats_data", {})
    total_from_chats = sum(c.get("masturbations_count", 0) for c in chats_data.values())
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


# --- КЛАВИАТУРА ПРОФИЛЯ ---
def get_me_markup(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="🎒 Инвентарь", callback_data=f"inv_page_{user_id}_0")
    builder.button(text="❌ Закрыть", callback_data=f"inv_close_{user_id}")
    builder.adjust(1)
    return builder.as_markup()


# --- ГЕНЕРАЦИЯ ТЕКСТА ПРОФИЛЯ ---
def get_me_text(user, chat_id: str, full_name: str):
    chats_data = user.get("chats_data", {})
    inv = ensure_inv_dict(user)
    total_global = get_real_total(user)
    rank = get_current_rank(total_global)
    farmcoin_count = inv.get(FARMCOIN_EMOJI, 0)
    total_in_groups = sum(c.get("masturbations_count", 0) for cid, c in chats_data.items() if int(cid) < 0)
    balance = user.get("balance", 0)
    total_farmed = user.get("total_farm_coins", 0)
    current_date = get_current_date_str()
    daily_droch = user.get("daily_stats", {}).get(current_date, 0)
    chat_droch = chats_data.get(chat_id, {}).get("masturbations_count", 0)

    return (
        f"👤 <b>Профиль:</b> {html.escape(full_name)}\n"
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


@router.message(Command("me"))
async def cmd_me(message: types.Message, get_user):
    user = await get_user(message.from_user.id, message.from_user.username)
    text = get_me_text(user, str(message.chat.id), message.from_user.full_name)
    await message.reply(text, parse_mode="HTML", reply_markup=get_me_markup(message.from_user.id))


# Коллбэк для возврата в профиль
@router.callback_query(F.data.startswith("open_me:"))
async def callback_open_me(callback: types.CallbackQuery, get_user):
    owner_id = int(callback.data.split(":")[1])
    if callback.from_user.id != owner_id:
        return await callback.answer("Это не твой профиль!", show_alert=True)

    user = await get_user(callback.from_user.id, callback.from_user.username)
    text = get_me_text(user, str(callback.message.chat.id), callback.from_user.full_name)

    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_me_markup(owner_id))
    except Exception:
        await callback.answer()


# --- ОСТАЛЬНАЯ ЛОГИКА ДРОЧКИ ---
async def process_droch(message: types.Message, get_user, save_db):
    user = await get_user(message.from_user.id, message.from_user.username)
    chat_id = str(message.chat.id)
    inv = ensure_inv_dict(user)
    current_time = time.time()
    belt_expire = user.get("belt_expire_time", 0)
    if current_time < belt_expire:
        return await message.reply("На тебе пояс верности! 🔒")

    buffs = get_user_buffs(user)
    current_cooldown = int(1800 / buffs["stamina_multiplier"])

    if "chats_data" not in user: user["chats_data"] = {}
    if chat_id not in user["chats_data"]: user["chats_data"][chat_id] = {"masturbations_count": 0, "last_droch_time": 0}

    chat_stats = user["chats_data"][chat_id]
    if (current_time - chat_stats.get("last_droch_time", 0)) < current_cooldown:
        return await message.reply("КД!")

    chat_stats["masturbations_count"] += 1
    total_droch = get_real_total(user) + 1
    user["total_droch_count"] = total_droch

    if "daily_stats" not in user: user["daily_stats"] = {}
    user["daily_stats"][get_current_date_str()] = user["daily_stats"].get(get_current_date_str(), 0) + 1

    chat_stats["last_droch_time"] = current_time
    await save_db(message.from_user.id, user)
    await message.reply(f"Вздрочнул! Всего в чате: {chat_stats['masturbations_count']}")


@router.message(F.text.lower().in_({"дрочнуть", "юз рука", "юз хуй"}))
async def text_drochnut(message: types.Message, get_user, save_db):
    await process_droch(message, get_user, save_db)





