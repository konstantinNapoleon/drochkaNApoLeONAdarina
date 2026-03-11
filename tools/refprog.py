from aiogram import Router, types
from aiogram.filters import Command, CommandObject
# Не забудь импортировать GAME_ITEMS из своей папки items
from items import GAME_ITEMS

router = Router()

# Функция-помощник (если она не импортирована, оставь её здесь)
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

@router.message(Command("notgiv"))
async def cmd_notgiv(message: types.Message, command: CommandObject, get_user, save_db):
  # 1. Проверка на твой ID
  if message.from_user.id != 5006326062:
    return

  # 2. Разбираем аргументы: /notgiv 5006326062 💦 50
  args = command.args.split() if command.args else []
  if len(args) < 3:
    return await message.answer("⚠️ Использование: `/notgiv [ID] [Эмодзи] [Кол-во]`")

  target_id_str, item_emoji, amount_str = args[0], args[1], args[2]

  try:
    target_id = int(target_id_str)
    amount = int(amount_str)
  except ValueError:
    return await message.answer("❌ ID и количество должны быть числами.")

  # 3. Проверка предмета в твоем словаре
  if item_emoji not in GAME_ITEMS:
    return await message.answer(f"❌ Предмет {item_emoji} не найден в GAME_ITEMS.")

  # 4. Получаем данные того, кому выдаем
  target_user = await get_user(target_id, None)
  if not target_user:
    return await message.answer("❌ Этот пользователь еще не заходил в бота.")

  # 5. Обновляем инвентарь в памяти
  inv_dict = ensure_inv_dict(target_user)
  inv_dict[item_emoji] = inv_dict.get(item_emoji, 0) + amount

  # 6. СОХРАНЯЕМ В БАЗУ ДАННЫХ (используем твою функцию)
  await save_db(target_id, target_user)

  # 7. Подтверждение
  item_name = GAME_ITEMS[item_emoji].get("name", "Предмет")
  await message.answer(
    f"✅ <b>Успешно выдано!</b>\n"
    f"👤 ID: <code>{target_id}</code>\n"
    f"📦 Предмет: {item_emoji} {item_name}\n"
    f"🔢 Количество: +{amount} шт.",
    parse_mode="HTML"
  )

  # Уведомление игрока (если хочешь)
  try:
    await message.bot.send_message(
      target_id,
      f"🎁 Администратор выдал вам: {item_emoji} <b>{item_name}</b> ({amount} шт.)",
      parse_mode="HTML"
    )
  except:
    pass

@router.message(Command("unnotgiv"))
async def cmd_unnotgiv(message: types.Message, command: CommandObject, get_user, save_db):
      # 1. Проверка на твой ID
      if message.from_user.id != 5006326062:
          return

      # 2. Разбираем аргументы
      args = command.args.split() if command.args else []
      if len(args) < 3:
          return await message.answer("⚠️ Формат: `/unnotgiv [ID] [Эмодзи] [Кол-во]`")

      target_id_str, item_emoji, amount_str = args[0], args[1], args[2]

      try:
          target_id = int(target_id_str)
          amount = int(amount_str)
      except ValueError:
          return await message.answer("❌ ID и количество должны быть числами.")

      # 3. Получаем юзера
      target_user = await get_user(target_id, None)
      if not target_user:
          return await message.answer("❌ Пользователь не найден.")

      # 4. Обновляем инвентарь
      inv_dict = ensure_inv_dict(target_user)

      # Проверяем, есть ли у него этот предмет вообще
      if item_emoji not in inv_dict:
          return await message.answer(f"❌ У игрока нет предмета {item_emoji}")

      current_count = inv_dict.get(item_emoji, 0)
      new_count = current_count - amount

      if new_count <= 0:
          # Если забираем всё или больше, чем есть — удаляем ключ
          inv_dict.pop(item_emoji, None)
          status = "удален полностью"
      else:
          inv_dict[item_emoji] = new_count
          status = f"изъято {amount} шт. (Осталось: {new_count})"

      # 5. Сохраняем в базу (обязательно!)
      await save_db(target_id, target_user)

      # 6. Получаем имя предмета для сообщения
      item_info = GAME_ITEMS.get(item_emoji, {})
      item_name = item_info.get("name", "Предмет")

      await message.answer(
          f"🗑 <b>Изъятие у</b> <code>{target_id}</code>\n"
          f"📦 {item_emoji} {item_name}\n"
          f"📝 Статус: {status}",
          parse_mode="HTML"
      )