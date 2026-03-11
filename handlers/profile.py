from aiogram import Router, F, types
from aiogram.filters import Command

router = Router()


@router.message(Command("start"), F.chat.type == "private")
async def cmd_start_private(message: types.Message, get_user, save_db):
    # Получаем данные пользователя
    user = await get_user(message.from_user.id, message.from_user.username)
    achievements = user.get("achievements", [])

    welcome_text = (
        "👋 Добро пожаловать в @droch_bot\n\n"
        "🔥 Заходи каждый день — получай бонусы. По команде /dailybonus@droch_bot\n\n"
        "🔥 Участвуй в ивентах — забирай эксклюзивы.\n\n"
        "📰 А так же у нас есть канал с новостями где ты можешь получить бонус коды для прокачки своего аккаунта: https://t.me/droch_information\n\n"
        "🤔 Хочешь обменяться валютой с другим участником бота? Отличное решение! Для этого у нас есть официальный чат: https://t.me/official_chat_droch"
    )

    # Проверяем и выдаем ачивку за регистрацию
    if "registration" not in achievements:
        achievements.append("registration")
        user["achievements"] = achievements
        await save_db(message.from_user.id, user)  # Сохраняем в базу

        # Дописываем сообщение о получении ачивки в конец текста
        welcome_text += "\n\n<i>🏆 Получена ачивка: ♦️ <b>Новая кровь</b></i>"

    # Обязательно добавляем parse_mode="HTML", чтобы курсив и жирный шрифт сработали
    await message.answer(
        welcome_text,
        disable_web_page_preview=True,
        parse_mode="HTML"
    )