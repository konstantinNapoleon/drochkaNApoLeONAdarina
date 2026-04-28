from aiogram import Router, types, F, Bot
from handlers.drochpass import ensure_user_pass_data, DAILY_QUESTS, QUEST_CHAT_ID, PEACH

router = Router()

CREATOR_ID = 5006326062
async def add_quest_progress(
    user_id: int,
    chat_id: int,
    username_text: str,
    quest_type: str,
    amount: int,
    get_user,
    save_db,
    bot: Bot
):
    user = await get_user(user_id, None)
    if not user:
        return

    user = ensure_user_pass_data(user)

    tasks = user["pass"]["quests"].get("tasks", {})
    updated = False

    for quest_id, data in tasks.items():
        if data["completed"]:
            continue

        quest_info = DAILY_QUESTS[quest_id]
        if quest_info["type"] == quest_type:
            data["progress"] = min(data["progress"] + amount, quest_info["target"])

            if data["progress"] >= quest_info["target"]:
                data["completed"] = True
                user["pass"]["xp"] += quest_info["reward"]

                text = quest_info["text"]
                if "{}" in text:
                    text = text.format(quest_info["target"])

                await bot.send_message(
                    chat_id,
                    f"✅ {username_text} выполнил задание: <b>{text}</b>\n"
                    f"Награда: +{quest_info['reward']} {PEACH}",
                    parse_mode="HTML"
                )

            updated = True

    if updated:
        await save_db(user_id, user)


@router.message(F.text & ~F.text.startswith("/"))
async def process_message_quest(message: types.Message, get_user, save_db, bot: Bot):
    # если нужно считать только в одном чате — оставь проверку
    if message.chat.id != QUEST_CHAT_ID:
        return

    await add_quest_progress(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        username_text=message.from_user.mention_html(),
        quest_type="messages",
        amount=1,
        get_user=get_user,
        save_db=save_db,
        bot=bot
    )


@router.message(F.text.func(lambda x: x and x.casefold() == "дать пизды"))
async def process_pizda_quest(message: types.Message, get_user, save_db, bot: Bot):
    if message.chat.id != QUEST_CHAT_ID:
        return

    if message.from_user.id != CREATOR_ID:
        return

    if not message.reply_to_message:
        return

    victim = message.reply_to_message.from_user
    if not victim:
        return

    await add_quest_progress(
        user_id=victim.id,
        chat_id=message.chat.id,
        username_text=victim.mention_html(),
        quest_type="pizda",
        amount=1,
        get_user=get_user,
        save_db=save_db,
        bot=bot
    )



