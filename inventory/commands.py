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



@router.message(Command("me"))
async def cmd_me(message: types.Message, get_user):
    user = await get_user(message.from_user.id, message.from_user.username)
    chat_id = str(message.chat.id)

    # Данные для вывода
    total_droch = user.get("total_droch_count", 0)
    rank = get_current_rank(total_droch)

    # Числа
    farmcoin_count = user.get("farm_coins", 0)  # Твои ФармКоины
    balance = user.get("balance", 0)
    total_farmed = user.get("total_farm_coins", 0)

    # Статистика дрочки
    current_date = get_current_date_str()
    daily_droch = user.get("daily_stats", {}).get(current_date, 0)
    chat_droch = user.get("chats_data", {}).get(chat_id, {}).get("masturbations_count", 0)

    # Формируем сообщение
    text = (
      f"👤 <b>Профиль:</b> {message.from_user.full_name}\n"
      f"━━━━━━━━━━━━━━\n"
      f"🎖 <b>Звание:</b> {rank}\n\n"

      f"{FARMCOIN} ФармКоин: <b>{farmcoin_count:,}</b>\n"  # Твоя строка

      f"💰 Баланс: <b>{balance:,}</b> 🪙\n"
      f"📈 Всего нафармлено: <b>{total_farmed:,}</b> 🪙\n\n"

      f"📊 <b>Статистика дрочки:</b>\n"
      f"├ В этом чате: <code>{chat_droch}</code>\n"
      f"├ За сегодня: <code>{daily_droch}</code>\n"
      f"└ Всего: <b>{total_droch}</b>"
    )

    await message.reply(text, parse_mode="HTML")




