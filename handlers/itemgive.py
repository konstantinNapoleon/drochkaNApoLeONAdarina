import html
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from items import GAME_ITEMS

router = Router()

# Функция для безопасного получения инвентаря в виде словаря
def get_inv_dict(user) -> dict:
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

@router.message(Command("give", "обмен", "передать"))
@router.message(F.text.lower().startswith("дать "))
async def cmd_give_item(message: types.Message, get_user, save_db, command: CommandObject = None):
  args = []
  if command and command.args:
    args = command.args.split()
  else:
    # Убираем слово "дать" и берем остальное
    parts = message.text.split()
    if len(parts) > 1:
      args = parts[1:]

  if not args:
    await message.answer(
      "ℹ️ <b>Как передать предмет:</b>\n\n"
      "<b>Вариант А (ответом):</b> <code>дать 🍹 5</code>\n"
      "<b>Вариант Б (по ID):</b> <code>дать 🍹 5 1234567</code>",
      parse_mode="HTML"
    )
    return

  item_emoji = args[0]
  if item_emoji not in GAME_ITEMS:
    return await message.answer("❌ Такого предмета не существует.")

  # Определяем количество
  amount = 1
  if len(args) >= 2:
    try:
      amount = int(args[1])
      if amount <= 0: return await message.answer("❌ Введи число больше 0.")
    except ValueError:
      pass

  # Определяем цель
  target_user_id = None
  if message.reply_to_message:
    target_user_id = message.reply_to_message.from_user.id
  elif len(args) >= 3:
    try:
      target_user_id = int(args[2])
    except ValueError:
      return await message.answer("❌ Неверный формат ID.")

  if not target_user_id or target_user_id == message.from_user.id:
    return await message.answer("❌ Нельзя передать самому себе или цель не найдена.")

  sender_user = get_user(message.from_user.id, message.from_user.username)
  target_user = get_user(target_user_id)

  if not target_user:
    return await message.answer("❌ Пользователь не найден в базе.")

  # ПЕРЕВОДИМ ИНВЕНТАРИ НА СЛОВАРИ
  sender_inv = get_inv_dict(sender_user)
  target_inv = get_inv_dict(target_user)

  # ПРОВЕРКА НАЛИЧИЯ (Мгновенно)
  current_count = sender_inv.get(item_emoji, 0)
  if current_count < amount:
    return await message.answer(f"❌ У тебя нет столько {item_emoji} (в наличии: {current_count})")

  # ПЕРЕДАЧА (Мгновенно, без циклов!)
  sender_inv[item_emoji] -= amount
  target_inv[item_emoji] = target_inv.get(item_emoji, 0) + amount

  # Очищаем ключ, если предметов стало 0 (чтобы не забивать базу)
  if sender_inv[item_emoji] <= 0:
    del sender_inv[item_emoji]

  save_db() # Обязательно сохраняем!

  item_name = GAME_ITEMS[item_emoji].get("name", "предмет")
  target_name = html.escape(message.reply_to_message.from_user.first_name if message.reply_to_message else f"ID {target_user_id}")

  await message.answer(
    f"✅ Ты передал <b>{amount} шт. {item_emoji} ({item_name})</b> {target_name}!",
    parse_mode="HTML"
  )