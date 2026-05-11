from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

# --- ОБНОВЛЕННЫЕ ИМПОРТЫ ---
from items import GAME_ITEMS
from handlers.bafus import ACHIEVEMENTS_LIST

# Импортируем новые данные и функции из других файлов пропуска
from .pass_data import (
    MAX_LEVEL,
    ULTRA_PASS_COST,
    PASS_LEVELS,
    CHERRY_EMOJI,
    SECTORS
)
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
    get_level_required_cherries,  # Обновленная функция
    get_sector_status  # Новая функция для секторов
)
from .pass_db import (
    get_pass_user,
    get_claimed_levels,
    get_or_create_today_tasks,
    claim_daily_bonus,
    has_claimed_daily_bonus,
    set_ultra_pass,
)

router = Router()

PHOTO_URL = "https://i.yapx.ru/dezXF.jpg"  # Можешь поменять на фото нового сезона
ALLOWED_CHAT_ID = -1003858938513  # ID чата для задания с сообщениями


# --- КЛАВИАТУРЫ ---

def get_main_pass_kb(is_ultra: bool, user_level: int):
    """Главное меню. Добавлена кнопка 'Секты'."""
    builder = InlineKeyboardBuilder()
    stage_to_open = max(1, user_level)

    builder.row(
        types.InlineKeyboardButton(
            text="🧩 Этапы", callback_data=f"pass:stages:{stage_to_open}")
    )
    # Новая кнопка для навигации по секторам
    builder.row(
        types.InlineKeyboardButton(text="🗂️ Секты", callback_data="pass:sectors_menu")
    )
    builder.row(
        types.InlineKeyboardButton(text="📝 Задания", callback_data="pass:tasks"),
        types.InlineKeyboardButton(text="🎈 Бонус", callback_data="pass:bonus"),
    )
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


def get_sectors_kb(user_level: int):
    """Новая клавиатура для отображения списка секторов."""
    builder = InlineKeyboardBuilder()
    # Сортируем ключи D, C, B, A
    for sector_id in sorted(SECTORS.keys(), reverse=True):
        sector_data = SECTORS[sector_id]
        status_emoji = get_sector_status(user_level, sector_id)

        button_text = f"[{status_emoji}] Сектор {sector_id}: {sector_data['name']}"
        builder.row(
            types.InlineKeyboardButton(
                text=button_text,
                callback_data=f"pass:sector_select:{sector_id}"
            )
        )
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="pass:menu"))
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
            types.InlineKeyboardButton(text="⬅️", callback_data=f"pass:stages:{level - 1}")
        )
    if level < MAX_LEVEL:
        nav_buttons.append(
            types.InlineKeyboardButton(text="➡️", callback_data=f"pass:stages:{level + 1}")
        )
    if nav_buttons:
        builder.row(*nav_buttons)
    if can_claim:
        builder.row(
            types.InlineKeyboardButton(text="✅ Забрать", callback_data=f"pass:claim:{level}")
        )
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="pass:menu"))
    return builder.as_markup()


def get_bonus_kb(can_claim: bool = True):
    builder = InlineKeyboardBuilder()
    if can_claim:
        builder.row(
            types.InlineKeyboardButton(text="🎁 Забрать бонус", callback_data="pass:bonus_claim")
        )
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="pass:menu"))
    return builder.as_markup()


def get_tasks_kb(tasks: list):
    builder = InlineKeyboardBuilder()
    for task in tasks:
        if task.get("is_completed") and not task.get("claimed"):
            reward = task['reward']
            builder.row(
                types.InlineKeyboardButton(
                    text=f"✅ Забрать {reward} {CHERRY_EMOJI}",
                    callback_data=f"pass:task_claim:{task['id']}",
                )
            )
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="pass:menu"))
    return builder.as_markup()


async def safe_edit_or_send_photo(message_obj: types.Message, text: str, reply_markup):
    """Универсальная функция для отправки/редактирования сообщений с фото."""
    if message_obj.photo:
        try:
            await message_obj.edit_caption(caption=text, parse_mode="HTML", reply_markup=reply_markup)
            return
        except TelegramBadRequest:
            pass
    try:
        await message_obj.edit_text(text=text, parse_mode="HTML", reply_markup=reply_markup)
    except TelegramBadRequest:
        await message_obj.answer_photo(photo=PHOTO_URL, caption=text, parse_mode="HTML", reply_markup=reply_markup)


# --- ОБРАБОТЧИКИ (ХЕНДЛЕРЫ) ---

async def render_pass_menu(target_message: types.Message, user_id: int):
    """Отображает главное меню Боевого Пропуска."""
    pass_user = await get_pass_user(user_id)
    cherries = int(pass_user.get("cherries", 0))  # Замена на cherries
    is_ultra = bool(pass_user.get("is_ultra", False))
    user_level = get_user_level(cherries)
    days_left = get_days_left()

    text = build_main_menu_text(user_level=user_level, is_ultra=is_ultra, days_left=days_left)
    await safe_edit_or_send_photo(message_obj=target_message, text=text,
                                  reply_markup=get_main_pass_kb(is_ultra, user_level))


@router.message(Command("pass"))
async def cmd_pass(message: types.Message):
    """Команда /pass, точка входа в Боевой Пропуск."""
    pass_user = await get_pass_user(message.from_user.id)
    cherries = int(pass_user.get("cherries", 0))  # Замена на cherries
    is_ultra = bool(pass_user.get("is_ultra", False))
    user_level = get_user_level(cherries)
    days_left = get_days_left()

    text = build_main_menu_text(user_level=user_level, is_ultra=is_ultra, days_left=days_left)
    await message.answer_photo(photo=PHOTO_URL, caption=text, parse_mode="HTML",
                               reply_markup=get_main_pass_kb(is_ultra, user_level))


@router.callback_query(F.data == "pass:menu")
async def cb_pass_menu(callback: types.CallbackQuery):
    """Кнопка 'Назад' в главное меню."""
    await render_pass_menu(callback.message, callback.from_user.id)
    await callback.answer()


# --- НОВЫЕ ОБРАБОТЧИКИ ДЛЯ СЕКТОРОВ ---

@router.callback_query(F.data == "pass:sectors_menu")
async def cb_sectors_menu(callback: types.CallbackQuery):
    """Отображает меню выбора секторов."""
    pass_user = await get_pass_user(callback.from_user.id)
    cherries = int(pass_user.get("cherries", 0))
    user_level = get_user_level(cherries)

    text = "Выберите сектор для просмотра или быстрого перехода."
    kb = get_sectors_kb(user_level)

    await safe_edit_or_send_photo(message_obj=callback.message, text=text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("pass:sector_select:"))
async def cb_sector_select(callback: types.CallbackQuery):
    """Обрабатывает выбор сектора. Перенаправляет на этап или показывает превью."""
    sector_id = callback.data.split(":")[2]

    pass_user = await get_pass_user(callback.from_user.id)
    cherries = int(pass_user.get("cherries", 0))
    user_level = get_user_level(cherries)

    status = get_sector_status(user_level, sector_id)
    sector_data = SECTORS[sector_id]

    if status == "🔒":
        text = f"🔐 <b>Предпросмотр Сектора {sector_id}</b>\n\nЭтот сектор пока заблокирован. Завершите предыдущий сектор, чтобы получить доступ."
        await callback.answer(f"Сектор {sector_id} заблокирован", show_alert=True)
        # Оставляем пользователя в том же меню
        kb = get_sectors_kb(user_level)
        await safe_edit_or_send_photo(message_obj=callback.message, text=text, reply_markup=kb)
    else:
        # Переход на первый уровень выбранного сектора
        target_level = min(sector_data['levels'])
        # "Подделываем" callback, чтобы передать управление хендлеру этапов
        callback.data = f"pass:stages:{target_level}"
        await cb_pass_stages(callback)
        # Отдельный callback.answer() не нужен, он будет в cb_pass_stages


# --- ОБНОВЛЕННЫЕ ОБРАБОТЧИКИ ---

@router.callback_query(F.data.startswith("pass:stages:"))
async def cb_pass_stages(callback: types.CallbackQuery):
    """Отображает конкретный этап."""
    level = int(callback.data.split(":")[2])
    pass_user = await get_pass_user(callback.from_user.id)
    claimed_levels_data = await get_claimed_levels(callback.from_user.id)
    is_ultra = bool(pass_user.get("is_ultra", False))
    cherries = int(pass_user.get("cherries", 0))  # Замена на cherries

    text = build_stage_text(level, cherries, claimed_levels_data, is_ultra)

    can_claim = False
    if cherries >= get_level_required_cherries(level):
        level_claims = claimed_levels_data.get(str(level), {})
        level_data = PASS_LEVELS.get(level, {})
        if not level_claims.get("regular"):
            can_claim = True
        elif is_ultra and "ultra_rewards" in level_data and not level_claims.get("ultra"):
            can_claim = True

    kb = get_stage_kb(level=level, can_claim=can_claim)
    await safe_edit_or_send_photo(message_obj=callback.message, text=text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "pass:tasks")
async def cb_pass_tasks(callback: types.CallbackQuery):
    """Отображает ежедневные задания."""
    pass_user = await get_pass_user(callback.from_user.id)
    is_ultra = bool(pass_user.get("is_ultra", False))
    tasks = await get_or_create_today_tasks(callback.from_user.id)

    text = build_tasks_text(tasks, get_hours_left_until_reset(), is_ultra)
    await safe_edit_or_send_photo(message_obj=callback.message, text=text, reply_markup=get_tasks_kb(tasks))
    await callback.answer()


@router.callback_query(F.data.startswith("pass:task_claim:"))
async def cb_pass_task_claim(callback: types.CallbackQuery):
    """Получение награды за ежедневное задание."""
    task_row_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id
    success, result = await claim_task_reward(user_id, task_row_id)

    if not success:
        return await callback.answer(str(result), show_alert=True)

    pass_user = await get_pass_user(user_id)
    is_ultra = bool(pass_user.get("is_ultra", False))
    tasks = await get_or_create_today_tasks(user_id)

    text = (f"✅ <b>Награда за задание получена!</b>\n\nТеперь у тебя: <b>{result}</b> {CHERRY_EMOJI}\n\n")
    text += build_tasks_text(tasks, get_hours_left_until_reset(), is_ultra)

    await safe_edit_or_send_photo(message_obj=callback.message, text=text, reply_markup=get_tasks_kb(tasks))
    await callback.answer("Награда получена!")


@router.callback_query(F.data == "pass:bonus")
async def cb_pass_bonus(callback: types.CallbackQuery):
    """Отображает меню ежедневного бонуса."""
    user_id = callback.from_user.id
    pass_user = await get_pass_user(user_id)
    is_ultra = pass_user.get("is_ultra", False)
    already_claimed = await has_claimed_daily_bonus(user_id)
    text = build_bonus_text(already_claimed=already_claimed, is_ultra=is_ultra)

    await safe_edit_or_send_photo(message_obj=callback.message, text=text,
                                  reply_markup=get_bonus_kb(can_claim=not already_claimed))
    await callback.answer()


@router.callback_query(F.data == "pass:bonus_claim")
async def cb_pass_bonus_claim(callback: types.CallbackQuery):
    """Получение ежедневного бонуса."""
    user_id = callback.from_user.id
    success, bonus_added, new_cherries = await claim_daily_bonus(user_id)

    if success:
        text = (f"✅ <b>Бонус получен!</b>\n\nТы забрал ежедневный бонус: {bonus_added} {CHERRY_EMOJI}\n"
                f"Теперь у тебя: <b>{new_cherries}</b> {CHERRY_EMOJI}")
        alert_text = "Бонус получен!"
    else:
        pass_user = await get_pass_user(user_id)
        is_ultra = pass_user.get("is_ultra", False)
        text = build_bonus_text(already_claimed=True, is_ultra=is_ultra)
        alert_text = "Ты уже получал бонус сегодня"

    await safe_edit_or_send_photo(message_obj=callback.message, text=text, reply_markup=get_back_kb())
    await callback.answer(alert_text)


@router.callback_query(F.data == "pass:buy_ultra")
async def cb_pass_buy_ultra(callback: types.CallbackQuery, get_user, save_db):
    """Покупка Ультра пропуска."""
    user_id = callback.from_user.id
    pass_user = await get_pass_user(user_id)
    if pass_user.get("is_ultra"):
        return await callback.answer("У тебя уже есть Ультра пропуск!", show_alert=True)

    user_data = await get_user(user_id, callback.from_user.username)
    inventory = user_data.get("inventory", {})
    frags = inventory.get("🪙", 0)

    if frags < ULTRA_PASS_COST:
        return await callback.answer(f"Недостаточно фрагов. Нужно {ULTRA_PASS_COST} 🪙", show_alert=True)

    inventory["🪙"] -= ULTRA_PASS_COST
    await set_ultra_pass(user_id, True)
    await save_db(user_id, user_data)

    text = "✅ <b>Поздравляем!</b>\n\nТы успешно приобрел Ультра пропуск."
    await safe_edit_or_send_photo(message_obj=callback.message, text=text, reply_markup=get_back_kb())
    await callback.answer("Ультра пропуск активирован!")


@router.callback_query(F.data == "pass:info")
async def cb_pass_info(callback: types.CallbackQuery):
    """Отображает информационное меню."""
    text = build_info_text()
    await safe_edit_or_send_photo(message_obj=callback.message, text=text, reply_markup=get_back_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("pass:claim:"))
async def cb_pass_claim(callback: types.CallbackQuery, get_user, save_db):
    """Получение награды за этап."""
    level = int(callback.data.split(":")[2])
    user_id = callback.from_user.id
    pass_user = await get_pass_user(user_id)
    claimed_levels_data = await get_claimed_levels(user_id)
    cherries = int(pass_user.get("cherries", 0))  # Замена на cherries
    is_ultra = pass_user.get("is_ultra", False)

    if cherries < get_level_required_cherries(level):
        return await callback.answer("Ты ещё не достиг этого уровня", show_alert=True)

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
        rewards_to_give.update(level_data.get("ultra_rewards", {}))

    if not rewards_to_give:
        return await callback.answer("Ошибка: награды для этого уровня не найдены.", show_alert=True)

    user = await get_user(user_id, callback.from_user.username)
    inv = user.get("inventory", {})
    for emoji, amount in rewards_to_give.items():
        inv[emoji] = inv.get(emoji, 0) + amount
    user["inventory"] = inv

    ach_id_to_give, ach_info = None, None
    if give_regular and "achievement" in level_data:
        ach_id_to_give = level_data.get("achievement")
        ach_info = ACHIEVEMENTS_LIST.get(ach_id_to_give)
        if ach_info:
            user_achievements = user.get("achievements", [])
            if ach_id_to_give not in user_achievements:
                user_achievements.append(ach_id_to_give)
                user["achievements"] = user_achievements

    await save_db(user_id, user)
    from .pass_db import claim_level
    await claim_level(user_id, level, regular=give_regular, ultra=give_ultra)

    rewards_lines = []
    for emoji, amount in rewards_to_give.items():
        item_name = GAME_ITEMS.get(emoji, {}).get("name", "Неизвестный предмет")
        line = f"— {emoji} {item_name}" + (f" x{amount}" if amount > 1 else "")
        rewards_lines.append(line)

    if ach_info:
        rewards_lines.append(f"— {ach_info['emoji']} Ачивка '{ach_info['name']}'")
    rewards_text = "\n".join(rewards_lines)

    text = (
        f"✅ <b>Награды за этап {level} получены!</b>\n\nВам было выдано:\n{rewards_text}\n\nПредметы уже в инвентаре 💜")
    await safe_edit_or_send_photo(message_obj=callback.message, text=text, reply_markup=get_back_to_stage_kb(level))
    await callback.answer("Награда получена!")


@router.message()
async def track_pass_messages(message: types.Message):
    """Отслеживает сообщения в чате для выполнения задания."""
    if not message.from_user or message.text and message.text.startswith("/") or message.chat.id != ALLOWED_CHAT_ID:
        return

    # Обновляем ID задания на 'chat_10' из нового пула заданий
    await progress_task(message.from_user.id, "chat_10", 1)