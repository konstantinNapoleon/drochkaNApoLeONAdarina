from aiogram import Router, types
from aiogram.filters import Command

router = Router() # Эта строка должна быть в каждом файле роутера!

@router.message(Command("start"))
async def cmd_start(message: types.Message, get_user):
 user = get_user(message.from_user.id) # Это автоматически создаст пользователя, если его нет
 await message.answer(f"Привет! Твой баланс: {user['balance']} 💰")