from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from items import GAME_ITEMS # Эта строчка может уже быть в pass_utils, но здесь она тоже нужна
from handlers.bafus import ACHIEVEMENTS_LIST


# Импортируем нужные данные
from .pass_data import MAX_LEVEL, ULTRA_PASS_COST, PASS_LEVELS
from .pass_tasks import claim_task_reward, progress_task
from .pass_texts import (
    build_main_menu_text,
    build_info_text,
    build_tasks_text,
    build_bonus_text,
)
from .pass_utils import (
    get_days_left,
    build_stage_text,
    get_hours_left_until_reset,
    get_user_level,
    get_level_required_peaches,
)
from .pass_db import (
    get_pass_user,
    get_claimed_levels,
    get_or_create_today_tasks,
    claim_daily_bonus,
    has_claimed_daily_bonus,
    set_ultra_pass,  # Добавляем импорт
)

router = Router()

PHOTO_URL = "https://i.yapx.ru/dezXF.jpg"
ALLOWED_CHAT_ID = -1003858938513


def get_main_pass_kb(is_ultra: bool, user_level: int):
  # Теперь функция принимает статус Ультра
    builder = InlineKeyboardBuilder()
    stage_to_open = max(1, user_level)
    builder.row(
        types.InlineKeyboardButton(
            text="🧩 Этапы", callback_data=f"pass:stages:{stage_to_open}")
    )
    builder.row(
        types.InlineKeyboardButton(text="📝 Задания", callback_data="pass:tasks"),
        types.InlineKeyboardButton(text="🎈 Бонус", callback_data="pass:bonus"),
    )
    # Если у пользователя еще нет Ультра пропуска, показываем кнопку покупки
    if not is_ultra:
        builder.row(
            types.InlineKeyboardButton(
                text=f"💠 Купить Ультра пропуск ({ULTRA_PASS_COST} 🪙)",
                callback_data="pass:buy_ultra",
            )
        )
    builder.row(
        types.InlineKeyboardButton(text="⁉️ Информация", callback_data="pass:info")
    )

    return builder.as_markup()

def get_back_to_stage_kb(level: int):
  builder = InlineKeyboardBuilder()
  builder.row(
    types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"pass:stages:{level}")
  )
  return builder.as_markup()


def get_back_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="⬅️ Назад", callback_data="pass:menu")
    )
    return builder.as_markup()


def get_stage_kb(level: int, can_claim: bool = False):
    builder = InlineKeyboardBuilder()

    nav_buttons = []

    if level > 1:
        nav_buttons.append(
            types.InlineKeyboardButton(
                text="⬅️", callback_data=f"pass:stages:{level - 1}"
            )
        )

    if level < MAX_LEVEL:
        nav_buttons.append(
            types.InlineKeyboardButton(
                text="➡️", callback_data=f"pass:stages:{level + 1}"
            )
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    if can_claim:
        builder.row(
            types.InlineKeyboardButton(
                text="✅ Забрать", callback_data=f"pass:claim:{level}"
            )
        )

    builder.row(
        types.InlineKeyboardButton(text="⬅️ Назад", callback_data="pass:menu")
    )

    return builder.as_markup()


def get_bonus_kb(can_claim: bool = True):
    builder = InlineKeyboardBuilder()

    if can_claim:
        builder.row(
            types.InlineKeyboardButton(
                text="🎁 Забрать бонус", callback_data="pass:bonus_claim"
            )
        )

    builder.row(
        types.InlineKeyboardButton(text="⬅️ Назад", callback_data="pass:menu")
    )

    return builder.as_markup()


def get_tasks_kb(tasks: list):
    builder = InlineKeyboardBuilder()

    for task in tasks:
        if task.get("is_completed") and not task.get("claimed"):
            builder.row(
                types.InlineKeyboardButton(
                    text=f"✅ Забрать {task['reward']} 🍑",
                    callback_data=f"pass:task_claim:{task['id']}",
                )
            )

    builder.row(
        types.InlineKeyboardButton(text="⬅️ Назад", callback_data="pass:menu")
    )
    return builder.as_markup()


async def safe_edit_or_send_photo(
    message_obj: types.Message, text: str, reply_markup
):
    if message_obj.photo:
        try:
            await message_obj.edit_caption(
                caption=text, parse_mode="HTML", reply_markup=reply_markup
            )
            return
        except TelegramBadRequest:
            pass

    try:
        await message_obj.edit_text(
            text=text, parse_mode="HTML", reply_markup=reply_markup
        )
    except TelegramBadRequest:
        await message_obj.answer_photo(
            photo=PHOTO_URL,
            caption=text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )


# Обновляем render_pass_menu и cmd_pass, чтобы они передавали is_ultra в клавиатуру
async def render_pass_menu(target_message: types.Message, user_id: int):
    pass_user = await get_pass_user(user_id)
    peaches = int(pass_user.get("peaches", 0))
    is_ultra = bool(pass_user.get("is_ultra", False))
    user_level = get_user_level(peaches)
    days_left = get_days_left()

    text = build_main_menu_text(
        user_level=user_level, is_ultra=is_ultra, days_left=days_left
    )

    await safe_edit_or_send_photo(
        message_obj=target_message, text=text, reply_markup=get_main_pass_kb(is_ultra, user_level)
    )


@router.message(Command("pass"))
async def cmd_pass(message: types.Message):
    pass_user = await get_pass_user(message.from_user.id)
    peaches = int(pass_user.get("peaches", 0))
    is_ultra = bool(pass_user.get("is_ultra", False))
    user_level = get_user_level(peaches)
    days_left = get_days_left()

    text = build_main_menu_text(
        user_level=user_level, is_ultra=is_ultra, days_left=days_left
    )

    await message.answer_photo(
        photo=PHOTO_URL,
        caption=text,
        parse_mode="HTML",
        reply_markup=get_main_pass_kb(is_ultra, user_level),  # Передаем статус
    )


@router.callback_query(F.data == "pass:menu")
async def cb_pass_menu(callback: types.CallbackQuery):
    await render_pass_menu(callback.message, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data.startswith("pass:stages:"))
async def cb_pass_stages(callback: types.CallbackQuery):
  level = int(callback.data.split(":")[2])

  pass_user = await get_pass_user(callback.from_user.id)
  claimed_levels_data = await get_claimed_levels(callback.from_user.id)
  is_ultra = bool(pass_user.get("is_ultra", False))
  peaches = int(pass_user.get("peaches", 0))

  text = build_stage_text(level, peaches, claimed_levels_data, is_ultra)

  # --- ИСПРАВЛЕНИЕ НАЧИНАЕТСЯ ЗДЕСЬ ---

  # Логика кнопки "Забрать"
  can_claim = False
  if peaches >= get_level_required_peaches(level):
    level_claims = claimed_levels_data.get(str(level), {})
    level_data = PASS_LEVELS.get(level, {})

    # Если не забрана обычная награда
    if not level_claims.get("regular"):
      can_claim = True
    # Или если есть ультра награда, куплен пропуск и она не забрана
    elif (is_ultra and "ultra_rewards" in level_data
       and not level_claims.get("ultra")):
      can_claim = True

  # Создание клавиатуры и отправка сообщения теперь ВНЕ условия
  kb = get_stage_kb(level=level, can_claim=can_claim)

  await safe_edit_or_send_photo(
    message_obj=callback.message, text=text, reply_markup=kb
  )
  await callback.answer()

  # --- ИСПРАВЛЕНИЕ ЗАКАНЧИВАЕТСЯ ЗДЕСЬ ---



@router.callback_query(F.data == "pass:tasks")
async def cb_pass_tasks(callback: types.CallbackQuery):
    pass_user = await get_pass_user(callback.from_user.id)
    is_ultra = bool(pass_user.get("is_ultra", False))
    tasks = await get_or_create_today_tasks(callback.from_user.id)

    # Передаем is_ultra в build_tasks_text
    text = build_tasks_text(tasks, get_hours_left_until_reset(), is_ultra)

    await safe_edit_or_send_photo(
        message_obj=callback.message, text=text, reply_markup=get_tasks_kb(tasks)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pass:task_claim:"))
async def cb_pass_task_claim(callback: types.CallbackQuery):
  task_row_id = int(callback.data.split(":")[2])
  user_id = callback.from_user.id

  success, result = await claim_task_reward(user_id, task_row_id)

  if not success:
    return await callback.answer(str(result), show_alert=True)

  # --- ИСПРАВЛЕНИЕ НАЧИНАЕТСЯ ЗДЕСЬ ---

  # 1. Получаем данные пользователя, чтобы знать про Ультра пасс
  pass_user = await get_pass_user(user_id)
  is_ultra = bool(pass_user.get("is_ultra", False))
  tasks = await get_or_create_today_tasks(user_id)

  text = (
    "✅ <b>Награда за задание получена!</b>\n\n"
    f"Теперь у тебя: <b>{result}</b> 🍑\n\n"
  )
  # 2. Передаем is_ultra в build_tasks_text
  text += build_tasks_text(tasks, get_hours_left_until_reset(), is_ultra)

  # --- ИСПРАВЛЕНИЕ ЗАКАНЧИВАЕТСЯ ЗДЕСЬ ---

  await safe_edit_or_send_photo(
    message_obj=callback.message, text=text, reply_markup=get_tasks_kb(tasks)
  )
  await callback.answer("Награда получена!")



# Меняем cb_pass_bonus чтобы передавать is_ultra в build_bonus_text
@router.callback_query(F.data == "pass:bonus")
async def cb_pass_bonus(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    pass_user = await get_pass_user(user_id)
    is_ultra = pass_user.get("is_ultra", False)
    already_claimed = await has_claimed_daily_bonus(user_id)
    text = build_bonus_text(already_claimed=already_claimed, is_ultra=is_ultra)

    await safe_edit_or_send_photo(
        message_obj=callback.message,
        text=text,
        reply_markup=get_bonus_kb(can_claim=not already_claimed),
    )

    await callback.answer()


# Обновляем cb_pass_bonus_claim, чтобы он правильно обрабатывал новый ответ от claim_daily_bonus
@router.callback_query(F.data == "pass:bonus_claim")
async def cb_pass_bonus_claim(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    pass_user = await get_pass_user(user_id)
    is_ultra = pass_user.get("is_ultra", False)

    success, bonus_added, new_peaches = await claim_daily_bonus(user_id)

    if success:
        text = (
            "✅ <b>Бонус получен!</b>\n\n"
            f"Ты забрал ежедневный бонус: {bonus_added} персиков 🍑\n"
            f"Теперь у тебя: <b>{new_peaches}</b> 🍑"
        )
        alert_text = "Бонус получен!"
    else:
        text = build_bonus_text(already_claimed=True, is_ultra=is_ultra)
        alert_text = "Ты уже получал бонус сегодня"

    await safe_edit_or_send_photo(
        message_obj=callback.message, text=text, reply_markup=get_back_kb()
    )

    await callback.answer(alert_text)


# Реализуем покупку Ультра пропуска
@router.callback_query(F.data == "pass:buy_ultra")
async def cb_pass_buy_ultra(callback: types.CallbackQuery, get_user, save_db):
    user_id = callback.from_user.id
    pass_user = await get_pass_user(user_id)

    if pass_user.get("is_ultra"):
        await callback.answer("У тебя уже есть Ультра пропуск!", show_alert=True)
        return

    user_data = await get_user(user_id, callback.from_user.username)
    inventory = user_data.get("inventory", {})
    frags = inventory.get("🪙", 0)

    if frags < ULTRA_PASS_COST:
        await callback.answer(
            f"Недостаточно фрагов. Нужно {ULTRA_PASS_COST} 🪙", show_alert=True
        )
        return

    # Списываем фраги и активируем пропуск
    inventory["🪙"] -= ULTRA_PASS_COST
    await set_ultra_pass(user_id, True)
    await save_db(user_id, user_data)

    text = (
        "✅ <b>Поздравляем!</b>\n\n"
        "Ты успешно приобрел Ультра пропуск.\n"
        "Все его преимущества теперь доступны для тебя!"
    )

    await safe_edit_or_send_photo(
        message_obj=callback.message, text=text, reply_markup=get_back_kb()
    )
    await callback.answer("Ультра пропуск активирован!")


@router.callback_query(F.data == "pass:info")
async def cb_pass_info(callback: types.CallbackQuery):
    text = build_info_text()
    await safe_edit_or_send_photo(
        message_obj=callback.message, text=text, reply_markup=get_back_kb()
    )
    await callback.answer()


# Обновляем cb_pass_claim для выдачи ультра-наград
@router.callback_query(F.data.startswith("pass:claim:"))
async def cb_pass_claim(callback: types.CallbackQuery, get_user, save_db):
    level = int(callback.data.split(":")[2])
    user_id = callback.from_user.id

    pass_user = await get_pass_user(user_id)
    claimed_levels_data = await get_claimed_levels(user_id)
    peaches = int(pass_user.get("peaches", 0))
    is_ultra = pass_user.get("is_ultra", False)

    if peaches < get_level_required_peaches(level):
        return await callback.answer("Ты ещё не достиг этого уровня", show_alert=True)

    from .pass_data import PASS_LEVELS
    level_data = PASS_LEVELS.get(level, {})
    level_claims = claimed_levels_data.get(str(level), {})

    give_regular = not level_claims.get("regular", False)
    has_ultra_reward = "ultra_rewards" in level_data and level_data["ultra_rewards"]
    give_ultra = is_ultra and has_ultra_reward and not level_claims.get("ultra", False)

    if not give_regular and not give_ultra:
        return await callback.answer("Все доступные награды уже получены", show_alert=True)

    rewards_to_give = {}
    if give_regular:
        rewards_to_give.update(level_data.get("rewards", {}))
    if give_ultra:
        ultra_rewards = level_data.get("ultra_rewards", {})
        for emoji, amount in ultra_rewards.items():
            rewards_to_give[emoji] = rewards_to_give.get(emoji, 0) + amount

    if not rewards_to_give:
        return await callback.answer("Ошибка: награды для этого уровня не найдены.", show_alert=True)

    user = await get_user(user_id, callback.from_user.username)
    inv = user.get("inventory", {})
    for emoji, amount in rewards_to_give.items():
        inv[emoji] = inv.get(emoji, 0) + amount
    user["inventory"] = inv

    # --- НОВАЯ ЛОГИКА ВЫДАЧИ АЧИВКИ ---
    ach_id_to_give = None
    ach_info = None
    # Если мы выдаем обычные награды и для уровня прописана ачивка
    if give_regular and "achievement" in level_data:
        ach_id_to_give = level_data.get("achievement")
        ach_info = ACHIEVEMENTS_LIST.get(ach_id_to_give)
        if ach_info:
            user_achievements = user.get("achievements", [])
            if ach_id_to_give not in user_achievements:
                user_achievements.append(ach_id_to_give)
                user["achievements"] = user_achievements
    # --- КОНЕЦ ЛОГИКИ ВЫДАЧИ АЧИВКИ ---

    await save_db(user_id, user)

    from .pass_db import claim_level
    await claim_level(user_id, level, regular=give_regular, ultra=give_ultra)

    # --- ОБНОВЛЕННОЕ ФИНАЛЬНОЕ СООБЩЕНИЕ ---
    rewards_lines = []
    for emoji, amount in rewards_to_give.items():
        item_name = GAME_ITEMS.get(emoji, {}).get("name", "Неизвестный предмет")
        line = f"— {emoji} {item_name}"
        if amount > 1:
            line += f" x{amount}"
        rewards_lines.append(line)

    # Добавляем ачивку в список выданных наград
    if ach_info:
        rewards_lines.append(f"— {ach_info['emoji']} Ачивка '{ach_info['name']}'")

    rewards_text = "\n".join(rewards_lines)

    text = (
        f"✅ <b>Награды за уровень {level} получены!</b>\n\n"
        f"Вам было выдано:\n{rewards_text}\n\n"
        "Предметы уже в инвентаре 💜"
    )

    await safe_edit_or_send_photo(
        message_obj=callback.message,
        text=text,
        reply_markup=get_back_to_stage_kb(level)
    )

    await callback.answer("Награда получена!")


@router.message()
async def track_pass_messages(message: types.Message):
    if not message.from_user:
        return

    if message.text and message.text.startswith("/"):
        return

    if message.chat.type not in ("group", "supergroup"):
        return

    if message.chat.id != ALLOWED_CHAT_ID:
        return

    await progress_task(message.from_user.id, "chat_50", 1)