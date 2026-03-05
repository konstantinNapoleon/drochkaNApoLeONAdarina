from aiogram import Router, F, types

router = Router()

# Твой ID (замени на свой настоящий)
ADMIN_ID = 5006326062


@router.message(F.text.lower().in_({"айди", "id"}), F.reply_to_message)
async def get_user_id(message: types.Message):
    # Проверка на админа
    if message.from_user.id != ADMIN_ID:
        return

    target_id = message.reply_to_message.from_user.id
    target_name = message.reply_to_message.from_user.first_name

    await message.answer(
        f"🆔 ID пользователя <b>{target_name}</b>: <code>{target_id}</code>\n\n"
        f"<i>Теперь ты можешь скопировать его (нажми на цифры) и использовать команду выдачи денег!</i>",
        parse_mode="HTML"
    )