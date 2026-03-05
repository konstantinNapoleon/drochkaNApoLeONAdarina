import math
import html
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from items import GAME_ITEMS

router = Router()
ITEMS_PER_PAGE = 10
FARMCOIN = "💰"


# --- НОВАЯ ЛОГИКА ИНВЕНТАРЯ (Словари) ---

def ensure_inv_dict(user) -> dict:
    """Гарантирует, что инвентарь — это словарь. Конвертирует старые списки."""
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


def get_farmcoins(user) -> int:
    """Просто берет число из словаря"""
    inv = ensure_inv_dict(user)
    return inv.get(FARMCOIN, 0)


def spend_farmcoins(user, amount: int) -> bool:
    """Списывает монеты (вычитанием числа)"""
    if amount <= 0: return True
    inv = ensure_inv_dict(user)
    current = inv.get(FARMCOIN, 0)

    if current < amount:
        return False

    inv[FARMCOIN] = current - amount
    return True


def add_item_to_inv(user, item_emoji: str, amount: int):
    """Добавляет предмет (прибавлением числа)"""
    inv = ensure_inv_dict(user)
    inv[item_emoji] = inv.get(item_emoji, 0) + amount


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (Магазин) ---

def get_shop_page(page: int = 0):
    sellable_items = [(k, v) for k, v in GAME_ITEMS.items() if v.get("price", 0) > 0]
    total_pages = math.ceil(len(sellable_items) / ITEMS_PER_PAGE)

    if not sellable_items:
        return "Магазин пуст.", None

    if page < 0: page = 0
    if page >= total_pages: page = total_pages - 1

    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    items_slice = sellable_items[start:end]

    text = "<b>Каталог магазина 🛍</b>\n"
    text += "<i>(Нажми на эмодзи, чтобы скопировать)</i>\n\n"

    for emoji, info in items_slice:
        price = info.get("price")
        name = info.get("name", emoji)
        text += f" • {price:,} 💰 — <code>{emoji}</code> <b>{name}</b>\n"

    text += f"\nСтраница {page + 1}/{total_pages}"

    builder = InlineKeyboardBuilder()
    nav_buttons = [
        types.InlineKeyboardButton(text="⏮", callback_data="shop_page:0"),
        types.InlineKeyboardButton(text="⬅️", callback_data=f"shop_page:{page - 1 if page > 0 else 0}"),
        types.InlineKeyboardButton(text="➡️",
                                   callback_data=f"shop_page:{page + 1 if page < total_pages - 1 else total_pages - 1}"),
        types.InlineKeyboardButton(text="⏭", callback_data=f"shop_page:{total_pages - 1}")
    ]
    builder.row(*nav_buttons)
    builder.row(types.InlineKeyboardButton(text="❌ Скрыть", callback_data="close_shop"))
    return text, builder.as_markup()


# --- ХЕНДЛЕРЫ ---

@router.message(Command("shop"))
async def cmd_shop(message: types.Message):
    text, kb = get_shop_page(0)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("shop_page:"))
async def process_shop_pagination(callback: types.CallbackQuery):
    page_idx = int(callback.data.split(":")[1])
    text, kb = get_shop_page(page_idx)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except:
        pass
    await callback.answer()


@router.callback_query(F.data == "close_shop")
async def close_shop(callback: types.CallbackQuery):
    await callback.message.delete()


@router.message(F.text.lower().startswith("купить"))
async def process_buy_command(message: types.Message):
    parts = message.text.split()
    if len(parts) < 3:
        return await message.answer("⚠️ Формат: <code>купить 🍃 50</code>", parse_mode="HTML")

    item_emoji = parts[1]
    try:
        amount = int(parts[2])
    except:
        return await message.answer("⚠️ Количество должно быть числом.")

    if amount <= 0: return await message.answer("⚠️ Минимум 1 шт.")
    if item_emoji not in GAME_ITEMS:
        return await message.answer("❌ Такого предмета нет в магазине.")

    item_info = GAME_ITEMS[item_emoji]
    total_price = item_info.get("price", 0) * amount

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="Подтвердить ✅", callback_data=f"buy_confirm:{item_emoji}:{amount}"),
        types.InlineKeyboardButton(text="Отменить ⛔️", callback_data="buy_cancel")
    )

    await message.reply(
        f"Вы уверены, что хотите купить {amount} {item_emoji} за {total_price:,} 💰?",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("buy_confirm:"))
async def buy_confirmed(callback: types.CallbackQuery, get_user, save_db):
    _, item_emoji, amount = callback.data.split(":")
    amount = int(amount)

    user = get_user(callback.from_user.id)
    item_info = GAME_ITEMS.get(item_emoji)
    total_price = item_info.get("price", 0) * amount

    # Списываем монеты
    if not spend_farmcoins(user, total_price):
        have = get_farmcoins(user)
        return await callback.answer(f"❌ Не хватает {total_price - have:,} 💰", show_alert=True)

    # Выдаем товар
    add_item_to_inv(user, item_emoji, amount)
    save_db()

    await callback.message.edit_text(f"✅ Ты купил {amount} {item_emoji} за {total_price:,} 💰!")
    await callback.answer()


@router.callback_query(F.data == "buy_cancel")
async def buy_cancel(callback: types.CallbackQuery):
    await callback.message.edit_text("❌ Покупка отменена.")