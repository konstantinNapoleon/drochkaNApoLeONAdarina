import html
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import FSInputFile  # <-- Добавили импорт для локальных файлов
from items import GAME_ITEMS

router = Router()

USE_RESPONSES = {
    "⚽": "Мячик для футбола, осторожно мошенники."
}

# Словарь с видео для предметов.
# Можно использовать:
# 1. Прямую ссылку на видео (https://...)
# 2. file_id из телеграма (самый быстрый способ)
# 3. Локальный файл на ПК/сервере через FSInputFile("путь_к_файлу.mp4")
USE_VIDEOS = {
    "⚽": "https://media.w3.org/2010/05/sintel/trailer.mp4",  # Пример ссылки
    "🍎": FSInputFile("videos/video_2026-03-03_21-52-42.mp4")  # Пример локального файла (папка videos, файл apple.mp4)
}


def ensure_inv_dict(user) -> dict:
    inv = user.get("inventory")
    if not isinstance(inv, dict):
        inv = {}
        user["inventory"] = inv
    return inv


async def process_item_use(message: types.Message, item_emoji: str, get_user, save_db):
    if item_emoji not in GAME_ITEMS:
        return await message.reply("❌ Такого предмета не существует.")

    user = get_user(message.from_user.id)
    inv_dict = ensure_inv_dict(user)

    item_count = inv_dict.get(item_emoji, 0)

    if item_count <= 0:
        return await message.reply("❌ У тебя нету такого предмета.")

    item_name = GAME_ITEMS[item_emoji].get("name", "Неизвестный предмет")

    # inv_dict[item_emoji] -= 1
    # if inv_dict[item_emoji] <= 0:
    #   del inv_dict[item_emoji]
    # save_db()

    response_text = USE_RESPONSES.get(item_emoji, f"Вы успешно использовали {html.escape(item_name)}.")
    video_data = USE_VIDEOS.get(item_emoji)

    # Проверяем, есть ли видео для этого предмета
    if video_data:
        # Отправляем видео, а текст ставим в описание (caption)
        await message.reply_video(video=video_data, caption=response_text, parse_mode="HTML")
    else:
        # Если видео нет, просто отправляем текст
        await message.reply(response_text, parse_mode="HTML")


# ... (ОБРАБОТЧИКИ cmd_use И text_use ОСТАЮТСЯ ТАКИМИ ЖЕ, КАК БЫЛИ) ...

@router.message(Command("use"))
async def cmd_use(message: types.Message, get_user, save_db):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.reply("Укажи предмет. Пример: /use ⚽")
    await process_item_use(message, args[1].strip(), get_user, save_db)


@router.message(F.text.lower().startswith("юз "))
async def text_use(message: types.Message, get_user, save_db):
    item_emoji = message.text[3:].strip()
    if not item_emoji:
        return await message.reply("Укажи предмет. Пример: юз ⚽")
    await process_item_use(message, item_emoji, get_user, save_db)