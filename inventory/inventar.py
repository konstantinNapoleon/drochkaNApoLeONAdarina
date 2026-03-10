import html
import math
import datetime
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import CommandObject

from items import GAME_ITEMS

router = Router()

ITEMS_PER_PAGE = 15
FARMCOIN_EMOJI = "💰"

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

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

def get_inventory_data(user_inventory: dict):
    formatted_items = []
    for item_emoji, count in user_inventory.items():
        if count <= 0: continue
        item_info = GAME_ITEMS.get(item_emoji, {"name": "Неизвестный предмет"})
        item_name = item_info.get("name", "Неизвестный предмет")
        if item_emoji == FARMCOIN_EMOJI:
            continue
        formatted_items.append(f"• {count} <code>{item_emoji}</code> {html.escape(item_name)}")
    formatted_items.sort()
    return formatted_items

def create_inventory_kb(current_page: int, total_pages: int):
    builder = InlineKeyboardBuilder()
    buttons = []
    if current_page > 0:
        buttons.append(types.InlineKeyboardButton(text="⬅️", callback_data=f"inv_page_{current_page - 1}"))
    buttons.append(types.InlineKeyboardButton(text=f"{current_page + 1}/{total_pages}", callback_data="none"))
    if current_page < total_pages - 1:
        buttons.append(types.InlineKeyboardButton(text="➡️", callback_data=f"inv_page_{current_page + 1}"))

    builder.row(*buttons)
    builder.row(types.InlineKeyboardButton(text="❌ Закрыть", callback_data="inv_close"))
    return builder.as_markup()

# --- ХЕНДЛЕРЫ ИНВЕНТАРЯ ---

@router.message(Command("inventory", "инв", "inv"))
async def cmd_inventory_grid(message: types.Message, get_user):
    user = await get_user(message.from_user.id, message.from_user.username)
    inv_dict = ensure_inv_dict(user)

    farmcoin_count = inv_dict.get(FARMCOIN_EMOJI, 0)
    formatted_items = get_inventory_data(inv_dict)

    if not formatted_items and farmcoin_count <= 0:
        return await message.answer("🎒 <b>Твой инвентарь пуст!</b>", parse_mode="HTML")

    total_pages = max(1, math.ceil(len(formatted_items) / ITEMS_PER_PAGE))
    page_items = formatted_items[:ITEMS_PER_PAGE]
    inventory_render = "\n".join(page_items) if page_items else "<i>Предметов нет</i>"

    name = html.escape(message.from_user.first_name or "Игрок")
    response = (
        f"🎒 Твой инвентарь, <b>{name}</b>\n\n"
        f"{FARMCOIN_EMOJI} ФармКоин: <b>{farmcoin_count:,}</b>\n\n"
        f"{inventory_render}"
    )

    await message.answer(response, parse_mode="HTML", reply_markup=create_inventory_kb(0, total_pages))

@router.callback_query(F.data.startswith("inv_page_"))
async def process_inventory_page(callback: types.CallbackQuery, get_user):
    page = int(callback.data.split("_")[2])
    # ДОБАВЛЕН await
    user = await get_user(callback.from_user.id, callback.from_user.username)
    inv_dict = ensure_inv_dict(user)

    farmcoin_count = inv_dict.get(FARMCOIN_EMOJI, 0)
    formatted_items = get_inventory_data(inv_dict)

    total_pages = max(1, math.ceil(len(formatted_items) / ITEMS_PER_PAGE))
    page = max(0, min(page, total_pages - 1))

    start_idx = page * ITEMS_PER_PAGE
    page_items = formatted_items[start_idx:start_idx + ITEMS_PER_PAGE]
    inventory_render = "\n".join(page_items) if page_items else "<i>Предметов нет</i>"

    name = html.escape(callback.from_user.first_name or "Игрок")
    response = (
        f"🎒 Твой инвентарь, <b>{name}</b>\n\n"
        f"{FARMCOIN_EMOJI} ФармКоин: <b>{farmcoin_count:,}</b>\n\n"
        f"{inventory_render}"
    )

    try:
        await callback.message.edit_text(response, parse_mode="HTML", reply_markup=create_inventory_kb(page, total_pages))
    except Exception:
        await callback.answer()

@router.callback_query(F.data == "inv_close")
async def process_close_inventory(callback: types.CallbackQuery):
    await callback.message.delete()

# --- БОНУС-КОДЫ ---

BONUS_CODES = {
  "SORRY": {
    "rewards": {"💰": 15000, "🎂": 10, "💦": 777},
    "limit": 100,
    "used_count": 0,
    "expires": datetime.datetime(2026, 5, 1),
    "claimed_by": set()
  },

  "UKRAINE": {
    "rewards": {"🇺🇦": 1},
    "limit": 100,
    "used_count": 0,
    "expires": datetime.datetime(2027, 12, 31),
    "claimed_by": set()
  }
}

@router.message(Command("bonuscode", "промо"))
async def process_bonus(message: types.Message, command: CommandObject, get_user, save_db):
    if not command.args:
        return await message.reply("⚠️ <b>Введи бонус-код!</b>\nПример: <code>/bonuscode START</code>", parse_mode="HTML")

    code_input = command.args.upper().strip()
    user_id = message.from_user.id

    if code_input not in BONUS_CODES:
        return await message.reply("❌ Такого бонус-кода не существует.")

    bonus = BONUS_CODES[code_input]
    if datetime.datetime.now() > bonus["expires"]:
        return await message.reply("⌛ Срок действия этого кода уже истек.")

    if bonus["used_count"] >= bonus["limit"]:
        return await message.reply("🚫 Лимит активаций этого кода исчерпан.")

    if user_id in bonus["claimed_by"]:
        return await message.reply("🤨 Ты уже активировал этот бонус-код!")

    # ДОБАВЛЕН await
    user = await get_user(user_id, message.from_user.username)
    inv = ensure_inv_dict(user)

    rewards = bonus.get("rewards", {})
    reward_list_text = []
    for item_emoji, amount in rewards.items():
        inv[item_emoji] = inv.get(item_emoji, 0) + amount
        item_info = GAME_ITEMS.get(item_emoji, {})
        item_name = item_info.get("name", "предмет")
        reward_list_text.append(f"• {item_emoji} <b>{item_name}</b> — {amount} шт.")

    bonus["used_count"] += 1
    bonus["claimed_by"].add(user_id)

    # ДОБАВЛЕН await
    await save_db(user_id, user)

    rewards_str = "\n".join(reward_list_text)
    await message.reply(
        f"✅ <b>Успешно активировано!</b>\n\n"
        f"🎁 <b>Вы получили:</b>\n{rewards_str}\n\n"
        f"📦 Все предметы добавлены в ваш инвентарь.",
        parse_mode="HTML"
    )







