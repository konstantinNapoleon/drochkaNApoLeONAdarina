from datetime import datetime, timezone, timedelta
import time
import asyncio
import logging
from aiogram import Router

router = Router()

MSK_TZ = timezone(timedelta(hours=3))
AVTOROB_INTERVAL = 30  # Интервал в секундах для теста


def get_current_date_str():
    return datetime.now(MSK_TZ).strftime("%Y-%m-%d")


async def avtorob_scheduler_task(bot, get_all_users, save_db):
    print("[🤖 Робот-Инфо] Фоновый планировщик успешно запущен!")
    logging.info("Фоновый планировщик Avtorob 3.14 запущен.")

    while True:
        try:
            # 1. Загружаем пользователей
            all_users = await get_all_users()
            current_time = time.time()

            # Лог для проверки работы цикла
            print(f"[🤖 Робот-Инфо] Сканирую базу данных... Всего пользователей: {len(all_users)}")

            for user_id_str, user_data in all_users.items():
                try:
                    user_id = int(user_id_str)
                except ValueError:
                    continue

                is_active = user_data.get("avtorob_active", False)
                saved_chat_id = user_data.get("avtorob_chat_id")

                # Если у этого пользователя включен робот
                if is_active and saved_chat_id:
                    last_time = user_data.get("last_avtorob_time", 0)
                    time_passed = current_time - last_time

                    print(
                        f" -> Пользователь {user_id}: Робот АКТИВЕН. Прошло времени: {int(time_passed)} сек. (Нужно: {AVTOROB_INTERVAL} сек.)")

                    # Проверяем, пришло ли время срабатывания
                    if time_passed >= AVTOROB_INTERVAL:
                        chat_id = str(saved_chat_id)
                        print(f" -> 🎉 Время пришло! Начисляю дрочку пользователю {user_id} в чат {chat_id}...")

                        # Начисляем дрочку
                        if "chats_data" not in user_data:
                            user_data["chats_data"] = {}
                        if chat_id not in user_data["chats_data"]:
                            user_data["chats_data"][chat_id] = {
                                "masturbations_count": 0,
                                "last_droch_time": 0,
                                "chat_name": "Группа"
                            }

                        user_data["chats_data"][chat_id]["masturbations_count"] += 1

                        total_from_chats = sum(
                            c.get("masturbations_count", 0) for c in user_data["chats_data"].values()
                        )
                        user_data["total_droch_count"] = max(user_data.get("total_droch_count", 0), total_from_chats)

                        if "daily_stats" not in user_data:
                            user_data["daily_stats"] = {}
                        today_str = get_current_date_str()
                        user_data["daily_stats"][today_str] = user_data["daily_stats"].get(today_str, 0) + 1

                        # Сдвигаем таймер и сохраняем
                        user_data["last_avtorob_time"] = current_time
                        await save_db(user_id, user_data)
                        print(f" -> Данные пользователя {user_id} сохранены в БД.")

                        # Пробуем написать в ЛС
                        try:
                            print(f" -> Попытка отправить сообщение в ЛС {user_id}...")
                            await bot.send_message(
                                chat_id=user_id,
                                text="К тебе пришел 🤖 Avtorob 3.14 и подрочил 1 раз."
                            )
                            print(f" -> ✅ Успешно отправлено в ЛС {user_id}!")
                        except Exception as pm_err:
                            print(f" -> ❌ Ошибка отправки в ЛС {user_id}: {pm_err}")
                            logging.warning(f"Не удалось отправить ЛС пользователю {user_id}: {pm_err}")

        except Exception as e:
            print(f"[🤖 Робот-Ошибка] Ошибка в главном цикле планировщика: {e}")
            logging.error(f"Ошибка в работе планировщика Avtorob: {e}")

        # Сон на 10 секунд во время тестирования
        await asyncio.sleep(10)




