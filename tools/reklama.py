import asyncio
from aiogram import types, Bot, Router
from aiogram.filters import Command
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

# Твой ID администратора
ADMIN_ID = 5006326062


@router.message(Command("post"))
async def cmd_post(message: types.Message, bot: Bot, get_all_users):
    # 1. Проверка на админа
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ У тебя нет прав администратора.")

    # --- НАСТРОЙКИ РАССЫЛКИ ---
    PHOTO_URL = "https://i.yapx.ru/dLWDX.jpg"
    link_text = "Если вас нет в наших ресурсах, то скорее нажминайте кнопку и вступайте 👇"

    # Создаем кнопки напрямую через InlineKeyboardMarkup (так надежнее)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Канал", url="https://t.me/droch_information"),
            InlineKeyboardButton(text="Чат", url="https://t.me/official_chat_droch")
        ]
    ])
    # ---------------------------

    # 3. Собираем всех получателей
    try:
        # Проверяем, нужно ли ждать (await) получения юзеров
        all_users = await get_all_users()
    except Exception as e:
        return await message.answer(f"❌ Ошибка при получении базы: {e}")

    if not all_users:
        return await message.answer("❌ База данных пуста.")

    targets = set()

    # Универсальный сбор ID (подходит и для списка, и для словаря)
    if isinstance(all_users, dict):
        for user_id, user_data in all_users.items():
            try:
                targets.add(int(user_id))
                if isinstance(user_data, dict) and "chats_data" in user_data:
                    for chat_id in user_data["chats_data"].keys():
                        targets.add(int(chat_id))
            except:
                continue
    elif isinstance(all_users, list):
        for user_id in all_users:
            try:
                targets.add(int(user_id))
            except:
                continue

    await message.answer(f"📢 Начинаю рассылку для {len(targets)} целей...")

    sent = 0
    errors = 0

    # 4. Цикл рассылки
    for target_id in targets:
        try:
            await bot.send_photo(
                chat_id=target_id,
                photo=PHOTO_URL,
                caption=link_text,
                reply_markup=kb,
                parse_mode="HTML"
            )
            sent += 1
            # Пауза для обхода спам-фильтра
            await asyncio.sleep(0.05)

        except TelegramForbiddenError:
            errors += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await bot.send_photo(target_id, photo=PHOTO_URL, caption=link_text, reply_markup=kb, parse_mode="HTML")
                sent += 1
            except:
                errors += 1
        except Exception:
            errors += 1

    await message.answer(f"✅ Рассылка завершена!\n🖼 Доставлено: {sent}\n❌ Ошибок: {errors}")