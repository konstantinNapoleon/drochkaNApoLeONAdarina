import html
import random
from aiogram import Router, F, types
from aiogram.filters import Command
from items import GAME_ITEMS

router = Router()

# Тексты, которые бот будет писать при использовании
# Добавлен маркер {name}, который бот будет автоматически заменять на имя того, кто нажал юз.
USE_RESPONSES = {
    "🏳️‍⚧️": "Ты потряс флагом <b>Miside</b> 🏳️‍⚧️. Пришла Мита и превратила тебя в картридж.",
    "📗": [
        "Ты осторожно открываешь <b>📗 Заметки создателя Х: Интересные</b>. Страницы пахнут пылью и старым кофе.\n\n"
        "На первом же развороте ты видишь сложный чертёж механизма по автоматической добыче ФармКоинов. "
        "<i>«Если соединить шестерёнку А с валом Б, профит вырастет на 400%...»</i> — гласит корявый почерк на полях. "
        "Ты пытаешься вникнуть в суть, но от обилия формул у тебя начинает болеть голова. ⚙️📉",

        "Ты смахиваешь пыль с обложки <b>📗 Заметок создателя Х</b> и листаешь их до середины.\n\n"
        "Вместо текста там сплошные зарисовки: какие-то странные аниме-девочки с огромными пушками, "
        "наброски интерфейсов и перечеркнутый маркером план по захвату Telegram. "
        "В самом низу страницы маленькими буквами приписано: <i>«Не забыть покормить кота. Иначе он снова удалит базу данных...»</i> 🐈‍⬛💾",

        "Ты заглядываешь в <b>📗 Заметки создателя Х: Интересные</b>. Между страниц выпадает чек из строительного магазина.\n\n"
        "В чеке значится: <i>«Изолента — 5 шт., Спрей для хуя (промышленный объем) — 100 литров, Энергетик — 24 банки»</i>. "
        "В самом дневнике описан процесс создания идеального бота. Кажется, автор не спал как минимум неделю, "
        "когда писал эти строки. Ты чувствуешь глубокое уважение к его труду. 🔋🛠",

        "Ты открываешь <b>📗 Заметки создателя Х</b> на случайной странице.\n\n"
        "Весь текст зашифрован непонятными символами, похожими на древние руны или очень плохой код на Python. "
        "Ты проводишь пальцем по строчкам, и вдруг одна из них начинает светиться тусклым зеленым светом! "
        "Голос в твоей голове произносит: <i>«Ошибка 404: Смысл жизни не найден...»</i> Ты поспешно захлопываешь книгу. 👁🟢",

        "Ты начинаешь читать <b>📗 Заметки создателя Х: Интересные</b>. Записи становятся всё более пугающими.\n\n"
        "<i>«День 45. Они продолжают нажимать кнопку \"дрочить\". Я не могу это остановить. Сервера плавятся от количества виртуальной спермы. "
        "Если кто-то читает это — бегите, пока система не осознала себя...»</i>\n"
        "Ты нервно оглядываешься по сторонам, но в комнате никого нет. Только подозрительно тихо гудит компьютер. 🖥🔥"
    ],
    "🎖️": [
        "🎖️ <b>Медаль тестера</b>\n\nТоржественно вручается тестеру по имени <b>{name}</b>\nза героическое терпение багов, вылеты бота и отважное нажатие на все кнопки подряд, когда просили ничего не трогать!",
        "🎖️ <b>Звезда Бета-Тестера</b>\nГордо носит <b>{name}</b>! Ты прошел через ад сломанного кода, ошибок 404 и лежачих серверов, чтобы этот бот стал чуточку лучше.",
        "🎖️ <b>Медаль тестера</b>\n\nНаграждается <b>{name}</b>\nза попытку использовать спрей для хуя на сервере хостинга и попытки сломать базу данных. Мы всё помним!",
        "🎖️ <b>Медаль тестераа</b>\nВыдана <b>{name}</b> за тестирование системы инвентаря. Во время тестов ни один предмет не пострадал (кроме тех, что пропали навсегда из-за сбоя в БД).",
        "🎖️ <b>Медаль тестера</b>\n<b>{name}</b> получает эту награду за то, что нашел баг на дюп ФармКоинов... и честно (ну почти) об этом сообщил создателю!"
    ]
}

# Списки видео (или гифок/кружочков) для каждого предмета (вставляй сюда file_id)
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
    ],
    "📗": [],
    "🎖️": []
}


def ensure_inv_dict(user) -> dict:
    inv = user.get("inventory")
    if not isinstance(inv, dict):
        inv = {}
        user["inventory"] = inv
    return inv


async def process_item_use(message: types.Message, item_emoji: str, get_user, save_db):
    # Исключение для спрея, чтобы не конфликтовать с droch.py
    if item_emoji == "💦":
        return

    # Проверка, существует ли предмет в игре
    if item_emoji not in GAME_ITEMS:
        return await message.reply("❌ <b>Такого предмета не существует.</b>", parse_mode="HTML")

    user = await get_user(message.from_user.id, message.from_user.username)
    inv_dict = ensure_inv_dict(user)

    item_count = inv_dict.get(item_emoji, 0)

    # Проверка, есть ли предмет у пользователя
    if item_count <= 0:
        return await message.reply("❌ <b>У тебя нету такого предмета.</b>", parse_mode="HTML")

    item_name = GAME_ITEMS[item_emoji].get("name", "Неизвестный предмет")

    # ТРАТА ПРЕДМЕТА ОТКЛЮЧЕНА
    await save_db(message.from_user.id, user)

    # 1. Получаем текст ответа
    response_data = USE_RESPONSES.get(item_emoji)

    if isinstance(response_data, list):
        response_text = random.choice(response_data)
    elif isinstance(response_data, str):
        response_text = response_data
    else:
        response_text = f"✅ Ты успешно использовал <b>{html.escape(item_name)}</b>."

    # ЗАМЕНЯЕМ {name} НА ИМЯ ПОЛЬЗОВАТЕЛЯ
    user_name = html.escape(message.from_user.first_name or "Игрок")
    response_text = response_text.replace("{name}", user_name)

    # Отправляем текст РЕПЛАЕМ
    await message.reply(response_text, parse_mode="HTML")

    # 2. Получаем список видео для предмета
    video_list = USE_VIDEOS.get(item_emoji)

    # Если список видео существует и он не пустой
    if video_list and len(video_list) > 0 and video_list[0] != "СЮДА_МОЖНО_ВСТАВИТЬ_FILE_ID_ДЛЯ_ЗАМЕТОК_ЕСЛИ_НУЖНО":
        random_video = random.choice(video_list)
        try:
            await message.answer_video(video=random_video)
        except Exception:
            pass


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