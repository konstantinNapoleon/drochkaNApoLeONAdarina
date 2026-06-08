import html
from aiogram import Router, types, F
from aiogram.filters import Command

router = Router()

# Ключ для хранения ссылки на картинку в данных пользователя
PAINTING_IMAGE_KEY = "painting_image_url"


# --- КОМАНДА /set ---
@router.message(Command("set"))
async def cmd_set_painting(message: types.Message, get_user, save_db):
    """Устанавливает картинку для предмета 🖼 Картина"""
    user = await get_user(message.from_user.id, message.from_user.username)

    if not user:
        return await message.reply("❌ Ошибка получения данных пользователя.")

    # Проверяем, есть ли ответ на сообщение с фото
    if not message.reply_to_message:
        return await message.reply(
            "❌ <b>Ответь на сообщение с картинкой!</b>\n\n"
            "Отправь картинку, ответь на неё и напиши <code>/set</code>",
            parse_mode="HTML"
        )

    # Получаем фото из ответа
    photo = None
    if message.reply_to_message.photo:
        photo = message.reply_to_message.photo[-1]
    elif message.reply_to_message.animation:
        photo = message.reply_to_message.animation
    elif message.reply_to_message.document and message.reply_to_message.document.mime_type.startswith("image/"):
        photo = message.reply_to_message.document

    if not photo:
        return await message.reply(
            "❌ <b>Это не картинка!</b>\n\n"
            "Ответь на сообщение с изображением и напиши <code>/set</code>",
            parse_mode="HTML"
        )

    file_id = photo.file_id if hasattr(photo, "file_id") else None

    if not file_id:
        return await message.reply("❌ Не удалось получить картинку.")

    user[PAINTING_IMAGE_KEY] = file_id
    await save_db(message.from_user.id, user)

    await message.reply(
        "✅ <b>Картина установлена!</b>\n\n"
        "Теперь при использовании 🖼 <b>Картины худроочера</b> она будет показываться в чате.\n"
        "Используй: <code>/use 🖼</code> или <code>юз 🖼</code>",
        parse_mode="HTML"
    )


# --- КОМАНДА /clearpainting ---
@router.message(Command("clearpainting"))
async def cmd_clear_painting(message: types.Message, get_user, save_db):
    """Очищает установленную картинку"""
    user = await get_user(message.from_user.id, message.from_user.username)

    if not user:
        return await message.reply("❌ Ошибка получения данных пользователя.")

    if user.get(PAINTING_IMAGE_KEY):
        del user[PAINTING_IMAGE_KEY]
        await save_db(message.from_user.id, user)
        await message.reply("✅ <b>Картина очищена!</b>", parse_mode="HTML")
    else:
        await message.reply("ℹ️ У тебя не установлена картина.")


# --- ФУНКЦИЯ ДЛЯ ОТПРАВКИ КАРТИНЫ ---
async def send_painting(message: types.Message, get_user):
    """Отправляет установленную картину пользователя"""
    user = await get_user(message.from_user.id, message.from_user.username)

    if not user:
        return await message.reply("❌ Ошибка получения данных пользователя.")

    image_file_id = user.get(PAINTING_IMAGE_KEY)

    if not image_file_id:
        return await message.reply(
            "❌ <b>У тебя нет установленной картины!</b>\n\n"
            "Отправь картинку, ответь на неё командой <code>/set</code>, "
            "а затем используй <code>/use 🖼</code>",
            parse_mode="HTML"
        )

    await message.reply_photo(
        photo=image_file_id,
        caption=f"🍑 <b>Картина от {html.escape(message.from_user.full_name)}</b>",
        parse_mode="HTML"
    )