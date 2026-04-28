from aiogram import Router, types, F, Bot
from handlers.drochpass import add_quest_progress, QUEST_CHAT_ID

router = Router()
CREATOR_ID = 5006326062



# Квест: Получить пизды от создателя
@router.message(F.text.casefold() == "тебе пизда")
async def quest_pizda(message: types.Message, get_user, save_db, bot: Bot):
    if not message.reply_to_message or message.reply_to_message.from_user.id != CREATOR_ID:
        return

    if message.chat.id != QUEST_CHAT_ID:
        return

    await add_quest_progress(
        user_id=message.from_user.id,
        quest_type="pizda",
        amount=1,
        get_user=get_user,
        save_db=save_db,
        bot=bot
    )
    await message.reply("✅ Получено пизды от создателя! Задание засчитано.")


# Квест: Написать 50 сообщений
@router.message(F.text & ~F.text.startswith("/"))
async def quest_messages(message: types.Message, get_user, save_db, bot: Bot):
    if message.chat.id != QUEST_CHAT_ID:
        return

    await add_quest_progress(
        user_id=message.from_user.id,
        quest_type="messages",
        amount=1,
        get_user=get_user,
        save_db=save_db,
        bot=bot
    )
