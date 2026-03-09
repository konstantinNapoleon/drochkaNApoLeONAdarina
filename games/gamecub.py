import html
import random
from aiogram import Router, F, types
from aiogram.filters import Command
from items import GAME_ITEMS

router = Router()

# Тексты, которые бот будет писать при использовании
USE_RESPONSES = {
  "🏳️‍⚧️": "Ты потряс флагом <b>Miside</b> 🏳️‍⚧️. Пришла Мита и превратила тебя в картридж."
}

# Списки видео для каждого предмета (вставляй сюда file_id)
USE_VIDEOS = {
  "🏳️‍⚧️": [
    "BAACAgIAAxkBAAITCWmqsfEDYz4AAUy5uMAcbSCznQhxBwACvY0AAl4qWElS35gDG6jWCzoE",
    "BAACAgIAAxkBAAITHmmqucbBVJqIjOMj435UtnBSiOfyAAIWjgACXipYSXG1uEx8XyMmOgQ",
    "BAACAgIAAxkBAAITIGmque0kDcaFuCBvnfh83jCL2zpbAAIZjgACXipYSVcUCme0RwABjToE",
    "BAACAgIAAxkBAAITImmquiIq3Ri3sTdcClx7YHpuD5PjAAIejgACXipYSR78vNovn3k8OgQ"
  ],
  "🍎": [
    "FILE_ID_ЯБЛОКА_1",
    "FILE_ID_ЯБЛОКА_2"
  ]
}


def ensure_inv_dict(user) -> dict:
  """Гарантирует, что инвентарь — это словарь"""
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


async def process_item_use(message: types.Message, item_emoji: str, get_user, save_db):
  # Проверка, существует ли предмет в игре
  if item_emoji not in GAME_ITEMS:
    return await message.reply("❌ <b>Такого предмета не существует.</b>", parse_mode="HTML")

  # ТЕХНИЧЕСКАЯ ПРАВКА: добавлен await и username для получения данных
  user = await get_user(message.from_user.id, message.from_user.username)
  inv_dict = ensure_inv_dict(user)

  item_count = inv_dict.get(item_emoji, 0)

  # Проверка, есть ли предмет у пользователя
  if item_count <= 0:
    return await message.reply("❌ <b>У тебя нету такого предмета.</b>", parse_mode="HTML")

  item_name = GAME_ITEMS[item_emoji].get("name", "Неизвестный предмет")

  # === Логика траты предмета (ЕСЛИ НУЖНО) ===
  # Если хочешь, чтобы предмет исчезал, убери "#" ниже:
  # inv_dict[item_emoji] -= 1
  # if inv_dict[item_emoji] <= 0:
  #   del inv_dict[item_emoji]
  # ТЕХНИЧЕСКАЯ ПРАВКА: сохранение данных
  # await save_db(message.from_user.id, user)

  # 1. Получаем текст ответа
  response_text = USE_RESPONSES.get(item_emoji, f"✅ Вы успешно использовали <b>{html.escape(item_name)}</b>.")

  # Отправляем текст РЕПЛАЕМ
  await message.reply(response_text, parse_mode="HTML")

  # 2. Получаем список видео для предмета
  video_list = USE_VIDEOS.get(item_emoji)

  if video_list:
    random_video = random.choice(video_list)
    # Отправляем случайное видео просто в чат
    await message.answer_video(video=random_video)




