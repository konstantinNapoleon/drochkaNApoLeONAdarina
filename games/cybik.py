import random
import time
import asyncio
from aiogram import Router, F, types
from aiogram.filters import Command, CommandObject
from ivent.pass_tasks import progress_task

router = Router()


def ensure_inv_dict(user) -> dict:
  inv = user.get("inventory")
  if not isinstance(inv, dict):
    user["inventory"] = {}
  return user["inventory"]


@router.message(Command("dice"))
@router.message(F.text.lower().startswith("кубик"))
async def play_dice(message: types.Message, command: CommandObject, get_user, save_db):
  user_id = message.from_user.id
  user = await get_user(user_id, message.from_user.username)
  chat_id = str(message.chat.id)
  current_time = time.time()

  # --- ПРОВЕРКА ПОЯСА ВЕРНОСТИ ---
  belt_expire = user.get("belt_expire_time", 0)
  if current_time < belt_expire:
    remaining = int(belt_expire - current_time)
    hours = remaining // 3600
    minutes = (remaining % 3600) // 60
    return await message.reply(
      f"На тебе пояс верности! 🔒 Ты не можешь играть ещё <b>{hours}ч. {minutes}мин.</b>",
      parse_mode="HTML"
    )

  # --- ПРОВЕРКА НАЛИЧИЯ КУБИКА ---
  inv = ensure_inv_dict(user)
  if inv.get("🎲", 0) <= 0:
    return await message.reply("У тебя нет предмета 🎲 Кубик! Купи его или выбей в кейсе.")

  # Получаем ставку
  args = command.args if command and command.args else message.text.split()[-1]
  try:
    user_guess = int(args)
    if not (1 <= user_guess <= 6):
      raise ValueError
  except (ValueError, IndexError):
    return await message.reply("Напиши число от 1 до 6! Пример: <code>кубик 5</code>", parse_mode="HTML")

  # --- ОТПРАВКА КУБИКА ---
  dice_msg = await message.reply_dice(emoji="🎲")
  dice_value = dice_msg.dice.value

  # Ждем завершения анимации
  await asyncio.sleep(3.5)
  await progress_task(user_id, "dice_1", 1)


  if dice_value == user_guess:
    # --- ПОБЕДА ---
    reward = random.randint(7, 12)

    if "chats_data" not in user:
      user["chats_data"] = {}
    if chat_id not in user["chats_data"]:
      user["chats_data"][chat_id] = {"masturbations_count": 0}

    user["chats_data"][chat_id]["masturbations_count"] += reward
    new_total = user["chats_data"][chat_id]["masturbations_count"]

    # ВЫДАЧА АЧИВКИ "ПОБЕДИТЕЛЬ"
    user_achievements = user.get("achievements", [])
    achievement_added = False
    if "whore_winner" not in user_achievements:
      user_achievements.append("whore_winner")
      user["achievements"] = user_achievements
      achievement_added = True

    await save_db(user_id, user)

    result_text = (
      f"🎯 Ты победил!\n🤖 Тебе {reward} раз подрочила толпа шлюх.\n"
      f"Новое значение: <b>{new_total}</b>"
    )

    if achievement_added:
      result_text += "\n\n💋 <b>Новая ачивка: Победитель!</b>\n└ <i>Ты получил дрочки от шлюшек.</i>"

    await message.reply(result_text, parse_mode="HTML")

  else:
    # --- ПРОИГРЫШ ---
    penalty_time = 6 * 3600
    user["belt_expire_time"] = current_time + penalty_time
    user["lock_reason"] = None

    await save_db(user_id, user)
    await message.reply("❌ Ты проиграл! 🐷 Надел пояс верности на 6 часов.")




