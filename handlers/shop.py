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

def get_shop_page(user_id: int, page: int = 0):
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
    text += "<i>(Для покупки пиши: купить [эмодзи] [количество])</i>\n\n"

    for emoji, info in items_slice:
        price = info.get("price")
        name = info.get("name", emoji)
        desc = info.get("description", "Без описания")
        text += f" • {price:} 💰 — <code>{emoji}</code> <b>{name}</b>: {desc}\n"

    text += f"Страница {page + 1}/{total_pages}"

    builder = InlineKeyboardBuilder()

    # ВОЗВРАЩЕННЫЕ КНОПКИ
    nav_buttons = [
        types.InlineKeyboardButton(text="⏮", callback_data=f"shop_page:{user_id}:0"),
        types.InlineKeyboardButton(text="⬅️", callback_data=f"shop_page:{user_id}:{page - 1 if page > 0 else 0}"),
        types.InlineKeyboardButton(text="➡️",
                                   callback_data=f"shop_page:{user_id}:{page + 1 if page < total_pages - 1 else total_pages - 1}"),
        types.InlineKeyboardButton(text="⏭", callback_data=f"shop_page:{user_id}:{total_pages - 1}")
    ]

    builder.row(*nav_buttons)
    builder.row(types.InlineKeyboardButton(text="❌ Скрыть", callback_data=f"close_shop:{user_id}"))
    return text, builder.as_markup()


# --- ХЕНДЛЕРЫ ---

@router.message(Command("shop"))
@router.message(F.text.lower() == "каталог")
async def cmd_shop(message: types.Message):
    text, kb = get_shop_page(message.from_user.id, 0)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("shop_page:"))
async def process_shop_pagination(callback: types.CallbackQuery):
    _, owner_id, page_idx = callback.data.split(":")

    if callback.from_user.id != int(owner_id):
        return await callback.answer("Это не ваш магазин! Напишите «каталог».", show_alert=True)

    page_idx = int(page_idx)
    text, kb = get_shop_page(int(owner_id), page_idx)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("close_shop:"))
async def close_shop(callback: types.CallbackQuery):
    _, owner_id = callback.data.split(":")

    if callback.from_user.id != int(owner_id):
        return await callback.answer("Вы не можете закрыть чужой магазин!", show_alert=True)

    await callback.message.delete()


@router.message(F.text.lower().startswith("купить"))
async def process_buy_command(message: types.Message):
    parts = message.text.split()

    # Если написали просто "купить" без ничего
    if len(parts) < 2:
        return await message.answer("⚠️ Формат: <code>купить 💦</code> или <code>купить 💦 5</code>", parse_mode="HTML")

    item_emoji = parts[1]

    # Логика определения количества
    amount = 1
    if len(parts) >= 3:
        try:
            amount = int(parts[2])
        except ValueError:
            return await message.answer("⚠️ Количество должно быть числом.")

    if amount <= 0:
        return await message.answer("⚠️ Минимум 1 шт.")

    if item_emoji not in GAME_ITEMS:
        return await message.answer("❌ Такого предмета нет в магазине.")

    item_info = GAME_ITEMS[item_emoji]
    price = item_info.get("price", 0)

    if price <= 0:
        return await message.answer("❌ Этот предмет не продается.")

    total_price = price * amount

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="Подтвердить ✅",
                                   callback_data=f"buy_confirm:{message.from_user.id}:{item_emoji}:{amount}")
    )
    builder.row(
        types.InlineKeyboardButton(text="Отменить ⛔️", callback_data=f"buy_cancel:{message.from_user.id}")
    )

    await message.reply(
        f"Вы уверены, что хотите купить <b>{amount} {item_emoji} {item_info.get('name')}</b> за <b>{total_price:,}</b> 💰?",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("buy_confirm:"))
async def buy_confirmed(callback: types.CallbackQuery, get_user, save_db):
    _, owner_id, item_emoji, amount = callback.data.split(":")

    if callback.from_user.id != int(owner_id):
        return await callback.answer("Это не ваша покупка!", show_alert=True)

    amount = int(amount)
    user = await get_user(callback.from_user.id, callback.from_user.username or "player")
    item_info = GAME_ITEMS.get(item_emoji)

    if not item_info or item_info.get("price", 0) <= 0:
        return await callback.answer("❌ Этот предмет больше не продается.", show_alert=True)

    total_price = item_info.get("price") * amount

    if not spend_farmcoins(user, total_price):
        have = get_farmcoins(user)
        return await callback.answer(f"❌ У тебя {have:,} 💰. Не хватает {total_price - have:,} 💰", show_alert=True)

    add_item_to_inv(user, item_emoji, amount)
    await save_db(callback.from_user.id, user)

    await callback.message.edit_text(
        f"✅ Ты успешно купил <b>{amount} {item_emoji} {item_info.get('name')}</b> за <b>{total_price:,} 💰</b>!",
        parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("buy_cancel:"))
async def buy_canceled(callback: types.CallbackQuery):
    _, owner_id = callback.data.split(":")

    if callback.from_user.id != int(owner_id):
        return await callback.answer("Вы не можете отменить чужую покупку!", show_alert=True)

    await callback.message.edit_text("❌ Покупка отменена.")
    await callback.answer()