
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

# --- ОБНОВЛЕННЫЕ ИМПОРТЫ ---
from items import GAME_ITEMS
from handlers.bafus import ACHIEVEMENTS_LIST

# Импортируем все новые константы и функции
from .pass_data import (
    MAX_LEVEL,
    ULTRA_PASS_COST, MEGA_PASS_COST, MEGA_UPGRADE_COST, # Цены
    PASS_TIER_NORMAL, PASS_TIER_ULTRA, PASS_TIER_MEGA, # Уровни пропуска
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
    get_level_required_cherries,
    get_sector_status
)
# Заменяем set_ultra_pass на set_pass_tier
from .pass_db import (
    get_pass_user,
    get_claimed_levels,
    get_or_create_today_tasks,
    claim_daily_bonus,
    has_claimed_daily_bonus,
    set_pass_tier,
    set_auto_claim_status,
)

router = Router()
PREVIEW_MODE_CACHE = {}

PHOTO_URL = "https://i.yapx.ru/dk3UT.jpg"
ALLOWED_CHAT_ID = -1003858938513

# --- КЛАВИАТУРЫ (полностью переписана get_main_pass_kb) ---

def get_main_pass_kb(pass_tier: int, user_level: int):
    """Клавиатура главного меню, адаптированная под систему Tiers."""
    builder = InlineKeyboardBuilder()

    # Кнопки навигации
    builder.row(types.InlineKeyboardButton(text="🧩 Этапы", callback_data="pass:show_stages"))
    builder.row(types.InlineKeyboardButton(text="🗂️ Секты", callback_data="pass:sectors_menu"))
    builder.row(
        types.InlineKeyboardButton(text="📝 Задания", callback_data="pass:tasks"),
        types.InlineKeyboardButton(text="🎈 Бонус", callback_data="pass:bonus"),
    )

    # Кнопки покупки/улучшения
    if pass_tier == PASS_TIER_NORMAL:
        builder.row(
            types.InlineKeyboardButton(
                text=f"💠 Купить Ультра ({ULTRA_PASS_COST} 🪙)",
                callback_data="pass:buy:ultra"
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text=f"💎 Купить Мега ({MEGA_PASS_COST} 🪙)",
                callback_data="pass:buy:mega"
            )
        )
    elif pass_tier == PASS_TIER_ULTRA:
        builder.row(
            types.InlineKeyboardButton(
                text=f"💎 Улучшить до Мега ({MEGA_UPGRADE_COST} 🪙)",
                callback_data="pass:buy:upgrade_mega"
            )
        )

    # Кнопки информации и настроек
    info_button = types.InlineKeyboardButton(text="⁉️ Информация", callback_data="pass:info")
    if pass_tier > PASS_TIER_NORMAL:
        # Для Ультра и Мега добавляем кнопку настроек
        settings_button = types.InlineKeyboardButton(text="⚙️ Настройки", callback_data="pass:settings")
        builder.row(info_button, settings_button)
    else:
        builder.row(info_button)

    return builder.as_markup()

# --- НОВЫЕ ТЕКСТ И КЛАВИАТУРА ДЛЯ НАСТРОЕК ---

def build_settings_text(auto_claim_enabled: bool) -> str:
    """Создает текст для меню настроек."""
    status = "✅ Включен" if auto_claim_enabled else "❌ Выключен"
    return (
        "⚙️ <b>Настройки Боевого Пропуска</b>\\n\\n"
        "Здесь ты можешь управлять дополнительными функциями твоего премиум-пропуска.\\n\\n"
        "<b>Авто-сбор наград за задания:</b>\\n"
        f"— Статус: {status}\\n"
        "— Описание: когда эта опция включена, награды за выполненные ежедневные задания будут начисляться тебе автоматически, без необходимости нажимать кнопку \\\"Забрать\\\"."
    )

def get_settings_kb(auto_claim_enabled: bool) -> types.InlineKeyboardMarkup:
    """Создает клавиатуру для меню настроек."""
    builder = InlineKeyboardBuilder()
    toggle_text = "❌ Выключить авто-сбор" if auto_claim_enabled else "✅ Включить авто-сбор"
    builder.row(types.InlineKeyboardButton(text=toggle_text, callback_data="pass:settings:toggle_autoclaim"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="pass:menu"))
    return builder.as_markup()


def get_sectors_kb(user_level: int):
    builder = InlineKeyboardBuilder()
    for sector_id in sorted(SECTORS.keys(), reverse=True):
        sector_data = SECTORS[sector_id]
        status_emoji = get_sector_status(user_level, sector_id)
        button_text = f"[{status_emoji}] {sector_data['name']}"
        if sector_id != 'Бонус':
            button_text = f"Сектор {sector_id}: " + button_text

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
        nav_buttons.append(types.InlineKeyboardButton(text="⬅️", callback_data=f"pass:stages:{level - 1}"))
    if level < MAX_LEVEL:
        nav_buttons.append(types.InlineKeyboardButton(text="➡️", callback_data=f"pass:stages:{level + 1}"))
    if nav_buttons:
        builder.row(*nav_buttons)
    if can_claim:
        builder.row(types.InlineKeyboardButton(text="✅ Забрать", callback_data=f"pass:claim:{level}"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="pass:menu"))
    return builder.as_markup()

def get_bonus_kb(can_claim: bool = True):
    builder = InlineKeyboardBuilder()
    if can_claim:
        builder.row(types.InlineKeyboardButton(text="🎁 Забрать бонус", callback_data="pass:bonus_claim"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="pass:menu"))
    return builder.as_markup()

def get_tasks_kb(tasks: list, pass_tier: int): # <-- Добавляем pass_tier
    builder = InlineKeyboardBuilder()
    for task in tasks:
        if task.get("is_completed") and not task.get("claimed"):
            reward = task['reward']
            # --- Новая логика множителя ---
            if pass_tier == PASS_TIER_ULTRA:
                reward *= 2
            elif pass_tier == PASS_TIER_MEGA:
                reward *= 3
            # ---------------------------------
            builder.row(
                types.InlineKeyboardButton(
                    text=f"✅ Забрать {reward} {CHERRY_EMOJI}",
                    callback_data=f"pass:task_claim:{task['id']}",
                )
            )
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="pass:menu"))
    return builder.as_markup()


async def safe_edit_or_send_photo(message_obj: types.Message, text: str, reply_markup):
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

# --- ОБРАБОТЧИКИ (ХЕНДЛЕРЫ) (Переписаны для работы с pass_tier) ---

async def render_pass_menu(target_message: types.Message, user_id: int):
    pass_user = await get_pass_user(user_id)
    cherries = int(pass_user.get("cherries", 0))
    pass_tier = int(pass_user.get("pass_tier", PASS_TIER_NORMAL))
    user_level = get_user_level(cherries)
    days_left = get_days_left()

    text = build_main_menu_text(user_level=user_level, pass_tier=pass_tier, days_left=days_left)
    await safe_edit_or_send_photo(message_obj=target_message, text=text, reply_markup=get_main_pass_kb(pass_tier, user_level))

@router.message(Command("pass"))
async def cmd_pass(message: types.Message):
    pass_user = await get_pass_user(message.from_user.id)
    cherries = int(pass_user.get("cherries", 0))
    pass_tier = int(pass_user.get("pass_tier", PASS_TIER_NORMAL))
    user_level = get_user_level(cherries)
    days_left = get_days_left()

    text = build_main_menu_text(user_level=user_level, pass_tier=pass_tier, days_left=days_left)
    await message.answer_photo(photo=PHOTO_URL, caption=text, parse_mode="HTML", reply_markup=get_main_pass_kb(pass_tier, user_level))

@router.callback_query(F.data == "pass:menu")
async def cb_pass_menu(callback: types.CallbackQuery):
    await render_pass_menu(callback.message, callback.from_user.id)
    await callback.answer()

@router.callback_query(F.data == "pass:sectors_menu")
async def cb_sectors_menu(callback: types.CallbackQuery):
    pass_user = await get_pass_user(callback.from_user.id)
    cherries = int(pass_user.get("cherries", 0))
    user_level = get_user_level(cherries)
    text = "Выберите сектор для просмотра или быстрого перехода."
    kb = get_sectors_kb(user_level)
    await safe_edit_or_send_photo(message_obj=callback.message, text=text, reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("pass:sector_select:"))
async def cb_sector_select(callback: types.CallbackQuery):
    sector_id = callback.data.split(":")[2]
    user_id = callback.from_user.id
    pass_user = await get_pass_user(user_id)
    cherries = int(pass_user.get("cherries", 0))
    user_level = get_user_level(cherries)
    pass_tier = int(pass_user.get("pass_tier", PASS_TIER_NORMAL))

    status = get_sector_status(user_level, sector_id)
    sector_data = SECTORS[sector_id]

    if status == "🔒":
        PREVIEW_MODE_CACHE[user_id] = sector_id
        text = (
            f"🔐 <b>Предпросмотр Сектора {sector_id} активирован!</b>\n\n"
            "Теперь, нажав кнопку 'Этапы' в главном меню, "
            "ты увидишь уровни и награды этого сектора."
        )
        await safe_edit_or_send_photo(
            message_obj=callback.message,
            text=text,
            reply_markup=get_main_pass_kb(pass_tier, user_level)
        )
        await callback.answer("Режим предпросмотра активирован!")
    else:
        if status == '❌':
            await callback.answer("Вы вернулись в свою главу прохождения", show_alert=False)
        else:
            await callback.answer()
        target_level = min(sector_data['levels'])
        new_callback = callback.model_copy(update={'data': f"pass:stages:{target_level}"})
        await cb_pass_stages(new_callback)

@router.callback_query(F.data == "pass:show_stages")
async def cb_show_stages(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id in PREVIEW_MODE_CACHE:
        sector_id = PREVIEW_MODE_CACHE[user_id]
        sector_data = SECTORS[sector_id]
        target_level = min(sector_data['levels'])
        del PREVIEW_MODE_CACHE[user_id]
        await callback.answer(f"Предпросмотр сектора {sector_id}...")
    else:
        pass_user = await get_pass_user(user_id)
        cherries = int(pass_user.get("cherries", 0))
        user_level = get_user_level(cherries)
        target_level = max(1, user_level)
        await callback.answer()
    new_callback = callback.model_copy(update={'data': f"pass:stages:{target_level}"})
    await cb_pass_stages(new_callback)

@router.callback_query(F.data.startswith("pass:stages:"))
async def cb_pass_stages(callback: types.CallbackQuery):
    level = int(callback.data.split(":")[2])
    pass_user = await get_pass_user(callback.from_user.id)
    claimed_levels_data = await get_claimed_levels(callback.from_user.id)
    pass_tier = int(pass_user.get("pass_tier", PASS_TIER_NORMAL))
    cherries = int(pass_user.get("cherries", 0))
    text = build_stage_text(level, cherries, claimed_levels_data, pass_tier)

    can_claim = False
    if cherries >= get_level_required_cherries(level):
        level_claims = claimed_levels_data.get(str(level), {})
        level_data = PASS_LEVELS.get(level, {})
        if not level_claims.get("regular"):
            can_claim = True
        elif pass_tier > PASS_TIER_NORMAL and "ultra_rewards" in level_data and not level_claims.get("ultra"):
            can_claim = True
    kb = get_stage_kb(level=level, can_claim=can_claim)
    await safe_edit_or_send_photo(message_obj=callback.message, text=text, reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "pass:tasks")
async def cb_pass_tasks(callback: types.CallbackQuery):
    pass_user = await get_pass_user(callback.from_user.id)
    pass_tier = int(pass_user.get("pass_tier", PASS_TIER_NORMAL))
    tasks = await get_or_create_today_tasks(callback.from_user.id)
    text = build_tasks_text(tasks, get_hours_left_until_reset(), pass_tier)
    await safe_edit_or_send_photo(message_obj=callback.message, text=text, reply_markup=get_tasks_kb(tasks, pass_tier))
    await callback.answer()

@router.callback_query(F.data.startswith("pass:task_claim:"))
async def cb_pass_task_claim(callback: types.CallbackQuery):
    task_row_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id
    success, result = await claim_task_reward(user_id, task_row_id)
    if not success:
        return await callback.answer(str(result), show_alert=True)
    pass_user = await get_pass_user(user_id)
    pass_tier = int(pass_user.get("pass_tier", PASS_TIER_NORMAL))
    tasks = await get_or_create_today_tasks(user_id)
    text = (f"✅ <b>Награда за задание получена!</b>\n\nТеперь у тебя: <b>{result}</b> {CHERRY_EMOJI}\n\n")
    text += build_tasks_text(tasks, get_hours_left_until_reset(), pass_tier)
    await safe_edit_or_send_photo(message_obj=callback.message, text=text, reply_markup=get_tasks_kb(tasks, pass_tier))
    await callback.answer("Награда получена!")

@router.callback_query(F.data == "pass:bonus")
async def cb_pass_bonus(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    pass_user = await get_pass_user(user_id)
    pass_tier = int(pass_user.get("pass_tier", PASS_TIER_NORMAL))
    already_claimed = await has_claimed_daily_bonus(user_id)
    text = build_bonus_text(already_claimed=already_claimed, pass_tier=pass_tier)
    await safe_edit_or_send_photo(message_obj=callback.message, text=text, reply_markup=get_bonus_kb(can_claim=not already_claimed))
    await callback.answer()

@router.callback_query(F.data == "pass:bonus_claim")
async def cb_pass_bonus_claim(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    success, bonus_added, new_cherries = await claim_daily_bonus(user_id)
    if success:
        text = (f"✅ <b>Бонус получен!</b>\n\nТы забрал ежедневный бонус: {bonus_added} {CHERRY_EMOJI}\n"
                f"Теперь у тебя: <b>{new_cherries}</b> {CHERRY_EMOJI}")
        alert_text = "Бонус получен!"
    else:
        pass_user = await get_pass_user(user_id)
        pass_tier = int(pass_user.get("pass_tier", PASS_TIER_NORMAL))
        text = build_bonus_text(already_claimed=True, pass_tier=pass_tier)
        alert_text = "Ты уже получал бонус сегодня"
    await safe_edit_or_send_photo(message_obj=callback.message, text=text, reply_markup=get_back_kb())
    await callback.answer(alert_text)

# Новый обработчик для всех видов покупок
@router.callback_query(F.data.startswith("pass:buy:"))
async def cb_pass_buy(callback: types.CallbackQuery, get_user, save_db):
    action = callback.data.split(":")[2]
    user_id = callback.from_user.id
    pass_user = await get_pass_user(user_id)
    current_tier = int(pass_user.get("pass_tier", PASS_TIER_NORMAL))

    target_tier, cost, success_text = 0, 0, ""
    if action == "ultra" and current_tier == PASS_TIER_NORMAL:
        target_tier, cost, success_text = PASS_TIER_ULTRA, ULTRA_PASS_COST, "Ультра пропуск активирован!"
    elif action == "mega" and current_tier == PASS_TIER_NORMAL:
        target_tier, cost, success_text = PASS_TIER_MEGA, MEGA_PASS_COST, "Мега пропуск активирован!"
    elif action == "upgrade_mega" and current_tier == PASS_TIER_ULTRA:
        target_tier, cost, success_text = PASS_TIER_MEGA, MEGA_UPGRADE_COST, "Пропуск улучшен до Мега!"
    else:
        return await callback.answer("Действие недоступно или у вас уже есть этот пропуск!", show_alert=True)

    user_data = await get_user(user_id, callback.from_user.username)
    inventory = user_data.get("inventory", {})
    frags = inventory.get("🪙", 0)

    if frags < cost:
        return await callback.answer(f"Недостаточно фрагов. Нужно {cost} 🪙", show_alert=True)

    inventory["🪙"] -= cost
    await set_pass_tier(user_id, target_tier)
    await save_db(user_id, user_data)

    text = f"✅ <b>Поздравляем!</b>\n\n{success_text}"
    await safe_edit_or_send_photo(message_obj=callback.message, text=text, reply_markup=get_back_kb())
    await callback.answer(success_text)

# Новый обработчик для кнопки настроек
@router.callback_query(F.data == "pass:settings")
async def cb_pass_settings(callback: types.CallbackQuery):
    """Отображает меню настроек."""
    user_id = callback.from_user.id
    pass_user = await get_pass_user(user_id)

    if pass_user.get("pass_tier", 0) == PASS_TIER_NORMAL:
        return await callback.answer("Этот раздел доступен только для владельцев Ультра или Мега пропуска.",
                                     show_alert=True)

    auto_claim_enabled = pass_user.get("auto_claim_enabled", False)
    text = build_settings_text(auto_claim_enabled)
    kb = get_settings_kb(auto_claim_enabled)

    await safe_edit_or_send_photo(message_obj=callback.message, text=text, reply_markup=kb)
    await callback.answer()

    @router.callback_query(F.data == "pass:settings:toggle_autoclaim")
    async def cb_toggle_autoclaim(callback: types.CallbackQuery):
        """Переключает статус авто-сбора."""
        user_id = callback.from_user.id
        pass_user = await get_pass_user(user_id)

        if pass_user.get("pass_tier", 0) == PASS_TIER_NORMAL:
            return await callback.answer("Эта функция доступна только для владельцев Ультра или Мега пропуска.",
                                         show_alert=True)

        current_status = pass_user.get("auto_claim_enabled", False)
        new_status = not current_status

        await set_auto_claim_status(user_id, new_status)

        text = build_settings_text(new_status)
        kb = get_settings_kb(new_status)

        await safe_edit_or_send_photo(message_obj=callback.message, text=text, reply_markup=kb)
        status_text = "включен" if new_status else "выключен"
        await callback.answer(f"Авто-сбор наград {status_text}")


@router.callback_query(F.data == "pass:info")
async def cb_pass_info(callback: types.CallbackQuery):
    text = build_info_text()
    await safe_edit_or_send_photo(message_obj=callback.message, text=text, reply_markup=get_back_kb())
    await callback.answer()

@router.callback_query(F.data.startswith("pass:claim:"))
async def cb_pass_claim(callback: types.CallbackQuery, get_user, save_db):
    level = int(callback.data.split(":")[2])
    user_id = callback.from_user.id
    pass_user = await get_pass_user(user_id)
    claimed_levels_data = await get_claimed_levels(user_id)
    cherries = int(pass_user.get("cherries", 0))
    pass_tier = int(pass_user.get("pass_tier", PASS_TIER_NORMAL))

    if cherries < get_level_required_cherries(level):
        return await callback.answer("Ты ещё не достиг этого уровня", show_alert=True)

    level_data = PASS_LEVELS.get(level, {})
    level_claims = claimed_levels_data.get(str(level), {})
    give_regular = not level_claims.get("regular", False)
    has_ultra_reward = "ultra_rewards" in level_data and level_data["ultra_rewards"]
    give_ultra = pass_tier > PASS_TIER_NORMAL and has_ultra_reward and not level_claims.get("ultra", False)

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
    if not message.from_user or message.text and message.text.startswith("/") or message.chat.id != ALLOWED_CHAT_ID:
        return
    await progress_task(message.from_user.id, "chat_10", 1)