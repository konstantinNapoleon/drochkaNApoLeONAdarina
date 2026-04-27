import asyncio
import random
import time
import datetime
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from contextlib import suppress
from aiogram.exceptions import TelegramBadRequest

from items import GAME_ITEMS

router = Router()
PHOTO_URL = "https://i.yapx.ru/dezXF.jpg"


# --- ИНВЕНТАРЬ ---
def ensure_inv_dict(user) -> dict:
    inv = user.get("inventory")
    if not isinstance(inv, dict):
        user["inventory"] = {}
    return user["inventory"]


# --- КОНФИГ ---
PASS_LEVELS = {
    1: {"xp": 50, "rewards": [("currency", "💰", 20000)]},
    2: {"xp": 75, "rewards": [("item", "🚚", 1)]},
    3: {"xp": 100, "rewards": [("item", "🍃", 2026)]},
    4: {"xp": 125, "rewards": [("currency", "💰", 32000)]},
    5: {"xp": 150, "rewards": [("currency", "💰", 10000), ("item", "📓", 1), ("item", "🎁", 1)]},
    6: {"xp": 175, "rewards": [("currency", "💰", 50000), ("item", "🔑", 1)]},
    7: {"xp": 200, "rewards": [("item", "💎", 10)]},
    8: {"xp": 225, "rewards": [("item", "🎁", 2), ("item", "🔰", 1)]},
    9: {"xp": 250, "rewards": [("currency", "💰", 100000), ("item", "💐", 1)]},
    10: {"xp": 300, "choice": [("item", "🍌", 1), ("item", "🍆", 1)]},
}

DAILY_QUESTS_DB = [
    {"text": "Написать 50 сообщений в чат", "reward": 200},
    {"text": "Подрочить {} раз", "reward": 60, "dynamic": True},
    {"text": "Произвести 1 успешный трейд", "reward": 40},
    {"text": "Передать 1 предмет (/give)", "reward": 20},
    {"text": "Получить пизды от создателя", "reward": 150},
    {"text": "Использовать 30 спреев", "reward": 30}
]


class PassMenu(CallbackData, prefix="pass"):
    action: str
    level: int = 1


def get_pass_end_date(user_data):
    return "14 дней"  # Упрощенно


def ensure_user_pass_data(user_data: dict):
    if "pass" not in user_data:
        user_data["pass"] = {"level": 1, "xp": 0, "pass_type": "Обычный", "claimed_levels": [], "bonus_date": None,
                             "tasks": []}
    return user_data


# --- ХЕНДЛЕРЫ ---

@router.message(Command("pass"))
async def cmd_pass(message: types.Message, get_user):
    user = await get_user(message.from_user.id, message.from_user.username)
    p = ensure_user_pass_data(user)["pass"]

    text = (f"<b>ДРОЧ ПАСС</b>\n\n<b>Твой этап:</b> {p['level']}\n"
            f"<b>Пропуск:</b> {p['pass_type']}\n<b>Дней до окончания:</b> {get_pass_end_date(user)}")

    kb = InlineKeyboardBuilder()
    kb.button(text="Этапы", callback_data=PassMenu(action="view_levels", level=p['level']))
    kb.button(text="Задания", callback_data=PassMenu(action="view_quests"))
    kb.button(text="Бонус", callback_data=PassMenu(action="bonus"))
    kb.button(text="Купить Ультра пропуск", callback_data=PassMenu(action="buy"))
    kb.button(text="Информация", callback_data=PassMenu(action="info"))
    kb.adjust(1, 2, 1, 1)
    await message.answer_photo(photo=PHOTO_URL, caption=text, reply_markup=kb.as_markup())


@router.callback_query(PassMenu.filter())
async def handle_pass(query: types.CallbackQuery, callback_data: PassMenu, get_user, save_db):
    user = await get_user(query.from_user.id, query.from_user.username)
    p = ensure_user_pass_data(user)["pass"]

    if callback_data.action == "view_levels":
        lvl = callback_data.level
        data = PASS_LEVELS.get(lvl)
        status = "в процессе"
        if p["level"] > lvl: status = "ожидает сбор"
        if lvl in p.get("claimed_levels", []): status = "получено"

        text = f"📦 <b>Боевой Пропуск | Уровень {lvl}</b>\n\nНаграда: {data['rewards']}\nСтатус: {status}"
        kb = InlineKeyboardBuilder()
        kb.row(
            types.InlineKeyboardButton(text="⬅️", callback_data=PassMenu(action="view_levels", level=max(1, lvl - 1))),
            types.InlineKeyboardButton(text="➡️", callback_data=PassMenu(action="view_levels", level=min(10, lvl + 1))))
        if status == "ожидает сбор":
            kb.row(types.InlineKeyboardButton(text="Забрать", callback_data=PassMenu(action="claim", level=lvl)))
        kb.row(types.InlineKeyboardButton(text="Назад", callback_data=PassMenu(action="back")))
        await query.message.edit_caption(caption=text, reply_markup=kb.as_markup())

    if callback_data.action == "claim":
        lvl = callback_data.level
        inv = ensure_inv_dict(user)
        for _, item_id, count in PASS_LEVELS[lvl].get("rewards", []):
            inv[item_id] = inv.get(item_id, 0) + count
        p.setdefault("claimed_levels", []).append(lvl)
        await save_db(query.from_user.id, user)
        await query.answer("✅ Награда получена!", show_alert=True)
        await handle_pass(query, PassMenu(action="view_levels", level=lvl), get_user, save_db)

    if callback_data.action == "bonus":
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        if p.get("bonus_date") == today: return await query.answer("Уже получал!", show_alert=True)
        p["bonus_date"] = today
        p["xp"] += 50
        await save_db(query.from_user.id, user)
        await query.answer("🎁 +50 персиков!", show_alert=True)

    if callback_data.action == "back":
        text = f"<b>ДРОЧ ПАСС</b>\n\nЭтап: {p['level']}"
        kb = InlineKeyboardBuilder()
        kb.button(text="Этапы", callback_data=PassMenu(action="view_levels", level=p['level']))
        await query.message.edit_caption(caption=text, reply_markup=kb.as_markup())

