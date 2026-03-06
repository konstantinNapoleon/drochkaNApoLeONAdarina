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
        "BAACAgIAAxkBAAITCWmqsfEDYz4AAUy5uMAcbSCznQhxBwACvY0AAl4qWElS35gDG6jWCzoE",  # Первое видео для мяча
        "BAACAgIAAxkBAAITHmmqucbBVJqIjOMj435UtnBSiOfyAAIWjgACXipYSXG1uEx8XyMmOgQ",  # Второе видео для мяча
        "BAACAgIAAxkBAAITIGmque0kDcaFuCBvnfh83jCL2zpbAAIZjgACXipYSVcUCme0RwABjToE",
        "BAACAgIAAxkBAAITImmquiIq3Ri3sTdcClx7YHpuD5PjAAIejgACXipYSR78vNovn3k8OgQ"# Третье видео для мяча
    ],
    "🍎": [
        "FILE_ID_ЯБЛОКА_1",
        "FILE_ID_ЯБЛОКА_2"
    ]
}


def ensure_inv_dict(user) -> dict:
    inv = user.get("inventory")
    if not isinstance(inv, dict):
        inv = {}
        user["inventory"] = inv
    return inv


async def process_item_use(message: types.Message, item_emoji: str, get_user, save_db):
    # Проверка, существует ли предмет в игре
    if item_emoji not in GAME_ITEMS:
        return await message.reply("❌ <b>Такого предмета не существует.</b>", parse_mode="HTML")

    user = get_user(message.from_user.id)
    inv_dict = ensure_inv_dict(user)

    item_count = inv_dict.get(item_emoji, 0)

    # Проверка, есть ли предмет у пользователя
    if item_count <= 0:
        return await message.reply("❌ <b>У тебя нету такого предмета.</b>", parse_mode="HTML")

    item_name = GAME_ITEMS[item_emoji].get("name", "Неизвестный предмет")

    # === Логика траты предмета (если нужно, чтобы он исчезал) ===
    # inv_dict[item_emoji] -= 1
    # if inv_dict[item_emoji] <= 0:
    #   del inv_dict[item_emoji]
    # save_db()

    # 1. Получаем текст ответа (или стандартный, если его нет в словаре)
    response_text = USE_RESPONSES.get(item_emoji, f"✅ Вы успешно использовали <b>{html.escape(item_name)}</b>.")

    # Отправляем текст РЕПЛАЕМ (с использованием HTML для жирного шрифта)
    await message.reply(response_text, parse_mode="HTML")

    # 2. Получаем список видео для предмета
    video_list = USE_VIDEOS.get(item_emoji)

    # Если список видео существует и он не пустой
    if video_list:
        # Выбираем одно случайное видео из списка
        random_video = random.choice(video_list)

        # Отправляем случайное видео БЕЗ реплая, просто в чат
        await message.answer_video(video=random_video)


# --- ОБРАБОТЧИКИ КОМАНД ---

@router.message(Command("use"))
async def cmd_use(message: types.Message, get_user, save_db):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.reply("Укажи предмет. Пример: <code>/use ⚽</code>", parse_mode="HTML")

    await process_item_use(message, args[1].strip(), get_user, save_db)


@router.message(F.text.lower().startswith("юз "))
async def text_use(message: types.Message, get_user, save_db):
    item_emoji = message.text[3:].strip()
    if not item_emoji:
        return await message.reply("Укажи предмет. Пример: <code>юз ⚽</code>", parse_mode="HTML")

    await process_item_use(message, item_emoji, get_user, save_db)