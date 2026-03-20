import html
from aiogram import Router, types, F
from aiogram.filters import Command

from handlers.droch import get_current_rank, get_current_date_str
from items import GAME_ITEMS  # Импортируем каталог для порядка

router = Router()

FARMCOIN = "💰"


@router.message(Command("si"))
async def cmd_inventory_grid(message: types.Message, get_user, save_db):
  user = await get_user(message.from_user.id, message.from_user.username)
  inv_data = user.get('inventory', {})

  # --- КОНВЕРТАЦИЯ (из списка в словарь, если нужно) ---
  if isinstance(inv_data, list):
    new_inv = {}
    for item in inv_data:
      new_inv[item] = new_inv.get(item, 0) + 1
    inv_data = new_inv
    user['inventory'] = inv_data
    await save_db(message.from_user.id, user)
  elif not isinstance(inv_data, dict):
    inv_data = {}

  # --- ПОЛУЧАЕМ ДАННЫЕ ПО ПОРЯДКУ КАТАЛОГА ---
  all_items = []

  # 1. Сначала проверяем монеты (они обычно вне общего списка предметов)
  farmcoins = inv_data.get(FARMCOIN, 0)
  if farmcoins > 0:
    all_items.append((farmcoins, FARMCOIN))

  # 2. Проходим по GAME_ITEMS, чтобы соблюсти последовательность каталога
  for item_emoji in GAME_ITEMS.keys():
    if item_emoji == FARMCOIN:
      continue
    count = inv_data.get(item_emoji, 0)
    if count > 0:
      all_items.append((count, item_emoji))

  # 3. Добавляем предметы, которых нет в каталоге (на всякий случай)
  for emoji, count in inv_data.items():
    if emoji not in GAME_ITEMS and emoji != FARMCOIN and count > 0:
      all_items.append((count, emoji))

  if not all_items:
    return await message.answer("🎒 Твой инвентарь пуст.")

  # --- РЕНДЕР СЕТКИ (Твой стиль сохранился) ---
  NUM_WIDTH = 5
  formatted_items = []
  for count, emoji in all_items:
    item_str = f"{str(count):>{NUM_WIDTH}} {emoji}"
    formatted_items.append(item_str)

  # Разбиваем на строки по 3 предмета
  rows = []
  for i in range(0, len(formatted_items), 3):
    rows.append(" | ".join(formatted_items[i:i + 3]))

  inventory_render = "\n".join(rows)

  # <pre> — обязателен для работы выравнивания
  response = f"<pre>{html.escape(inventory_render)}</pre>"
  await message.answer(response, parse_mode="HTML")








