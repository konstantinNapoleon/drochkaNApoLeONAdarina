from aiogram import Router, F, types
from aiogram.filters import Command

router = Router()


@router.message(Command("start"), F.chat.type == "private")
async def cmd_start_private(message: types.Message):
    welcome_text = (
        "👋 Добро пожаловать в @droch_bot\n\n"
        "🔥 Заходи каждый день — получай бонусы. По команде /dailybonus@droch_bot\n\n"
        "🔥 Участвуй в ивентах — забирай эксклюзивы.\n\n"
        "📰 А так же у нас есть канал с новостями где ты можешь получить бонус коды для прокачки своего аккаунта: https://t.me/droch_information\n\n"
        "🤔 Хочешь обменяться валютой с другим участником бота? Отличное решение! Для этого у нас есть официальный чат: https://t.me/official_chat_droch"
    )

    # disable_web_page_preview=True убирает огромные превью ссылок, чтобы сообщение выглядело аккуратно
    await message.answer(welcome_text, disable_web_page_preview=True)