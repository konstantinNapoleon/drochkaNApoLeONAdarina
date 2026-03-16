import asyncio
from aiogram import types, Bot, Router
from aiogram.filters import Command
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

# Твой ID администратора
ADMIN_ID = 5006326062


@router.message(Command("post"))
async def cmd_post(message: types.Message, bot: Bot, get_all_users):
    # 1. Проверка на админа
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ У тебя нет прав администратора.")

    # --- НАСТРОЙКИ РАССЫЛКИ ---
    PHOTO_URL = "https://yapx.ru/album/dLV6H.jpg"
    link_text = "Если вас нет в наших ресурсах, то скорее нажминайте кнопку и вступайте 👇"

    # Создаем кнопки
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="Канал", url="https://t.me/droch_information"),
        types.InlineKeyboardButton(text="Чат", url="https://t.me/official_chat_droch")
    )
    markup = builder.as_markup()
    # ---------------------------

    # 3. Собираем всех получателей
    all_users = await get_all_users()
    targets = set()

    for user_id, user_data in all_users.items():
        targets.add(user_id)
        if "chats_data" in user_data:
            for chat_id in user_data["chats_data"].keys():
                targets.add(int(chat_id))

    await message.answer(f"📢 Начинаю рассылку с кнопками для {len(targets)} чатов/юзеров...")

    sent = 0
    errors = 0

    # 4. Цикл рассылки
    for target_id in targets:
        try:
            await bot.send_photo(
                chat_id=target_id,
                photo=PHOTO_URL,
                caption=link_text,
                reply_markup=markup,
                parse_mode="HTML"
            )
            sent += 1
            await asyncio.sleep(0.05)  # Пауза против спам-фильтра

        except TelegramForbiddenError:
            errors += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await bot.send_photo(target_id, photo=PHOTO_URL, caption=link_text, reply_markup=markup,
                                     parse_mode="HTML")
                sent += 1
            except:
                errors += 1
        except Exception:
            errors += 1

    await message.answer(f"✅ Рассылка завершена!\n🖼 Фото доставлено: {sent}\n❌ Ошибок: {errors}")