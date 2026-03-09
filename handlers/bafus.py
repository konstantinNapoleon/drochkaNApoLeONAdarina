from aiogram import Router, types, F
from aiogram.filters import Command

router = Router()

# Список всех существующих ачивок в боте
ACHIEVEMENTS_LIST = {
    "first_droch": {"name": "✊ Первая дрочка", "desc": "Вы сделали это в первый раз!"},
    "rich_boy": {"name": "💰 Богач", "desc": "Накопить 100,000 монет"},
    "collector": {"name": "🎒 Коллекционер", "desc": "Собрать 10 предметов в инвентаре"}
}


@achievements_router.message(Command("achievements"))
@achievements_router.message(F.text.casefold() == "ачивки")
async def show_achievements(message: types.Message, get_user):
    user_data = await get_user(message.from_user.id, message.from_user.username)

    # Получаем список полученных ачивок (если его нет в базе — создаем пустой)
    user_achievements = user_data.get("achievements", [])

    text = "📜 **Ваши достижения:**\n\n"

    for key, info in ACHIEVEMENTS_LIST.items():
        if key in user_achievements:
            status = "✅"
            desc = info['desc']
        else:
            status = "🔒"
            desc = "???"  # Скрываем описание для интереса

        text += f"{status} **{info['name']}**\n└ {desc}\n\n"

    await message.answer(text)