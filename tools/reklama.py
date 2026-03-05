import asyncio
from aiogram import types, Bot
from aiogram.filters import Command
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram import Router, types

router = Router()

# Твой ID администратора
ADMIN_ID = 5006326062


@router.message(Command("post"))
async def cmd_post(message: types.Message, bot: Bot, get_all_users):
    # 1. Проверка на админа
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ У тебя нет прав администратора.")

    # --- НАСТРОЙКИ РАССЫЛКИ ---
    # Ссылка на фото (можно взять прямую ссылку из интернета или ID файла в TG)
    PHOTO_URL = "https://i.yapx.ru/dFN98.jpg"

    # Твой текст (в рассылке с фото лимит текста — 1024 символа!)
    link_text = (
        "🔥 <b>Важное обновление!</b>\n\n"
        "Не пропусти важную информацию в нашем канале!\n"
        "👉 <a href='https://t.me/droch_information'>ПОДПИСАТЬСЯ</a>"
    )
    # ---------------------------

    # 3. Собираем всех получателей
    all_users = get_all_users()
    targets = set()

    for user_id, user_data in all_users.items():
        targets.add(user_id)
        if "chats_data" in user_data:
            for chat_id in user_data["chats_data"].keys():
                targets.add(chat_id)

    await message.answer(f"📢 Начинаю рассылку с ФОТО для {len(targets)} чатов/юзеров...")

    sent = 0
    errors = 0

    # 4. Цикл рассылки
    for target_id in targets:
        try:
            # Используем send_photo вместо send_message
            await bot.send_photo(
                chat_id=target_id,
                photo=PHOTO_URL,
                caption=link_text,
                parse_mode="HTML"
            )
            sent += 1
            await asyncio.sleep(0.05)  # Пауза против спам-фильтра

        except TelegramForbiddenError:
            errors += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            # Повторная попытка после ожидания
            try:
                await bot.send_photo(target_id, photo=PHOTO_URL, caption=link_text, parse_mode="HTML")
                sent += 1
            except:
                errors += 1
        except Exception:
            errors += 1

    await message.answer(f"✅ Рассылка завершена!\n🖼 Фото доставлено: {sent}\n❌ Ошибок: {errors}")