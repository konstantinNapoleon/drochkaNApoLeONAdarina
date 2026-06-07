from datetime import datetime, timezone, timedelta
import time
import asyncio
import logging
import random
from aiogram import Router

router = Router()

MSK_TZ = timezone(timedelta(hours=3))
AVTOROB_INTERVAL = 3600 # 1 час


def get_current_date_str():
 return datetime.now(MSK_TZ).strftime("%Y-%m-%d")


async def avtorob_scheduler_task(bot, get_all_users, save_db):
 logging.info("Фоновый планировщик Avtorob 3.14 запущен на часовой интервал.")

 while True:
  try:
   all_users = await get_all_users()
   current_time = time.time()

   for user_id_str, user_data in all_users.items():
    try:
     user_id = int(user_id_str)
    except ValueError:
     continue

    is_active = user_data.get("avtorob_active", False)
    saved_chat_id = user_data.get("avtorob_chat_id")

    if is_active and saved_chat_id:
     last_time = user_data.get("last_avtorob_time", 0)

     if current_time - last_time >= AVTOROB_INTERVAL:
      chat_id = str(saved_chat_id)

      # Проверяем наличие вилки в инвентаре
      inventory = user_data.get("inventory", {})
      has_plug = isinstance(inventory, dict) and inventory.get("🔌", 0) > 0

      if has_plug:
       # Вилка НЕ списывается, просто даёт бонус от 4 до 7
       added_droch = random.randint(4, 7)
       text_msg = f"К тебе пришел 🤖 Avtorob 3.14 и подрочил {added_droch} раз за счёт 🔌 вилки."
      else:
       added_droch = 1
       text_msg = "К тебе пришел 🤖 Avtorob 3.14 и подрочил 1 раз."

      # Инициализируем структуры, если их нет
      if "chats_data" not in user_data:
       user_data["chats_data"] = {}
      if chat_id not in user_data["chats_data"]:
       user_data["chats_data"][chat_id] = {
        "masturbations_count": 0,
        "last_droch_time": 0,
        "chat_name": "Группа"
       }

      # Начисляем дрочки в чат (1 или от 4 до 7)
      user_data["chats_data"][chat_id]["masturbations_count"] += added_droch

      # Синхронизируем общий счет
      total_from_chats = sum(
       c.get("masturbations_count", 0) for c in user_data["chats_data"].values()
      )
      user_data["total_droch_count"] = max(user_data.get("total_droch_count", 0), total_from_chats)

      # Обновляем дневную статистику
      if "daily_stats" not in user_data:
       user_data["daily_stats"] = {}
      today_str = get_current_date_str()
      user_data["daily_stats"][today_str] = user_data["daily_stats"].get(today_str, 0) + added_droch

      # Обновляем время срабатывания и сохраняем в БД
      user_data["last_avtorob_time"] = current_time
      await save_db(user_id, user_data)

      # Отправляем уведомление в ЛС
      try:
       await bot.send_message(
        chat_id=user_id,
        text=text_msg
       )
      except Exception as pm_err:
       logging.warning(f"Не удалось отправить ЛС пользователю {user_id}: {pm_err}")

  except Exception as e:
   logging.error(f"Ошибка в работе планировщика Avtorob: {e}")

  await asyncio.sleep(10 if AVTOROB_INTERVAL < 60 else 60)





