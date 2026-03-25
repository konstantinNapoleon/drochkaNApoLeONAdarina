import time
import random
from aiogram import types, F, Router
from aiogram.filters import Command

router = Router()


@router.message(Command("xyu_up"))
@router.message(F.text.lower() == "растить хуй")
async def cmd_penis_growth(message: types.Message, get_user, save_db):
    user = await get_user(message.from_user.id, message.from_user.username)
    current_time = time.time()

    # Инициализация параметров, если их нет
    if "penis_size" not in user:
        user["penis_size"] = 10  # Начальный размер
    if "last_penis_growth" not in user:
        user["last_penis_growth"] = 0

    last_growth = user["last_penis_growth"]
    cooldown = 12 * 3600  # 12 часов в секундах

    if current_time - last_growth < cooldown:
        remaining = int(cooldown - (current_time - last_growth))
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        return await message.reply(
            f"❌ Твой агрегат ещё восстанавливается! \nПриходи через <b>{hours}ч. {minutes}мин.</b>",
            parse_mode="HTML"
        )

    # Логика роста (50/50)
    change_amount = 0
    if random.random() < 0.5:
        # УСПЕХ: растет на 1-5 см
        change_amount = random.randint(1, 12)
        user["penis_size"] += change_amount
        msg = f"❤️‍🔥 Твой хуй вырос на <b>{change_amount} см</b>! ✨ Новый размер — <b>{user['penis_size']} см</b>."
    else:
        # НЕУДАЧА: падает на 1-3 см
        change_amount = random.randint(1, 7)
        user["penis_size"] = max(1, user["penis_size"] - change_amount)  # Минимум 1 см
        msg = f"🔻 Твой хуй сократился на <b>{change_amount} см</b>! 💔 Новый размер — <b>{user['penis_size']} см</b>."

    user["last_penis_growth"] = current_time
    await save_db(message.from_user.id, user)

    await message.reply(msg, parse_mode="HTML")