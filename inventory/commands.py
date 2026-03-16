import html
from aiogram import Router, types, F
from aiogram.filters import Command

from handlers.droch import get_current_rank, get_current_date_str

router = Router()

FARMCOIN = "💰"


@router.message(Command("si"))
async def cmd_inventory_grid(message: types.Message, get_user, save_db):
  # ТЕХНИЧЕСКАЯ ПРАВКА: добавлен await и username
  user = await get_user(message.from_user.id, message.from_user.username)
  inv_data = user.get('inventory', {})

  # --- КОНВЕРТАЦИЯ (из списка в словарь, если нужно) ---
  if isinstance(inv_data, list):
    new_inv = {}
    for item in inv_data:
      new_inv[item] = new_inv.get(item, 0) + 1
    inv_data = new_inv
    user['inventory'] = inv_data
    # ТЕХНИЧЕСКАЯ ПРАВКА: добавлены аргументы и await
    await save_db(message.from_user.id, user)
  elif not isinstance(inv_data, dict):
    inv_data = {}

  # --- ПОЛУЧАЕМ ДАННЫЕ ---
  farmcoins = inv_data.get(FARMCOIN, 0)

  # Собираем остальные предметы (кроме монет)
  counts = {emoji: count for emoji, count in inv_data.items() if emoji != FARMCOIN and count > 0}

  # Собираем всё для отображения: сначала 💰, потом остальное
  all_items = []
  if farmcoins > 0:
    all_items.append((farmcoins, FARMCOIN))

  for emoji, count in counts.items():
    all_items.append((count, emoji))

  if not all_items:
    return await message.answer("🎒 Твой инвентарь пуст.")

  # --- РЕНДЕР СЕТКИ (Твой стиль сохранился) ---
  NUM_WIDTH = 5
  formatted_items = []
  for count, emoji in all_items:
    # Твоё форматирование выравнивания
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







