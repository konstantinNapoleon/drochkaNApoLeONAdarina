import asyncio
from aiogram import types, Bot, Router
from aiogram.filters import Command
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

router = Router()

# Твой ID администратора
ADMIN_ID = 5006326062

@router.message(Command("post"))
async def cmd_post(message: types.Message, bot: Bot, get_all_users):
  # 1. Проверка на админа
  if message.from_user.id != ADMIN_ID:
    return await message.answer("❌ У тебя нет прав администратора.")

  # --- НАСТРОЙКИ РАССЫЛКИ (Твой текст и фото) ---
  PHOTO_URL = "https://i.yapx.ru/dFN98.jpg"
  link_text = (
    "🔥 <b>Если вас еще нету в нашем канале, советую подписаться!</b>\n\n"
    "Информация уже на канале!\n"
    "👉 <a href='https://t.me/droch_information'>ПОДПИСАТЬСЯ</a>"
  )
  # ---------------------------

  # 3. Собираем всех получателей
  # ТЕХНИЧЕСКАЯ ПРАВКА: добавлен await
  all_users = await get_all_users()
  targets = set()

  for user_id, user_data in all_users.items():
    targets.add(user_id)
    if "chats_data" in user_data:
      # Превращаем ключи в инты, чтобы не было ошибок типа данных
      for chat_id in user_data["chats_data"].keys():
        targets.add(int(chat_id))

  await message.answer(f"📢 Начинаю рассылку с ФОТО для {len(targets)} чатов/юзеров...")

  sent = 0
  errors = 0

  # 4. Цикл рассылки
  for target_id in targets:
    try:
      # Используем send_photo как в твоем коде
      await bot.send_photo(
        chat_id=target_id,
        photo=PHOTO_URL,
        caption=link_text,
        parse_mode="HTML"
      )
      sent += 1
      # Небольшая пауза, чтобы Telegram не забанил за спам
      await asyncio.sleep(0.05)

    except TelegramForbiddenError:
      errors += 1
    except TelegramRetryAfter as e:
      # Если словили ограничение по скорости — ждем и пробуем еще раз
      await asyncio.sleep(e.retry_after)
      try:
        await bot.send_photo(target_id, photo=PHOTO_URL, caption=link_text, parse_mode="HTML")
        sent += 1
      except:
        errors += 1
    except Exception:
      errors += 1

  await message.answer(f"✅ Рассылка завершена!\n🖼 Фото доставлено: {sent}\n❌ Ошибок: {errors}")