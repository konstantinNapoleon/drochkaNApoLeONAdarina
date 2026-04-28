from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

from .pass_tasks import claim_task_reward, progress_task
from .pass_data import MAX_LEVEL
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
)

router = Router()

PHOTO_URL = "https://i.yapx.ru/dezXF.jpg"
ALLOWED_CHAT_ID = -1003858938513


def get_main_pass_kb():
    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(
            text="📦 Этапы",
            callback_data="pass:stages:1"
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="📋 Задания",
            callback_data="pass:tasks"
        ),
        types.InlineKeyboardButton(
            text="🎁 Бонус",
            callback_data="pass:bonus"
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="🔥 Купить Ультра пропуск",
            callback_data="pass:buy_ultra"
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="ℹ️ Информация",
            callback_data="pass:info"
        )
    )

    return builder.as_markup()


def get_back_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="pass:menu"
        )
    )
    return builder.as_markup()


def get_stage_kb(level: int, can_claim: bool = False):
    builder = InlineKeyboardBuilder()

    nav_buttons = []

    if level > 1:
        nav_buttons.append(
            types.InlineKeyboardButton(
                text="⬅️",
                callback_data=f"pass:stages:{level - 1}"
            )
        )

    if level < MAX_LEVEL:
        nav_buttons.append(
            types.InlineKeyboardButton(
                text="➡️",
                callback_data=f"pass:stages:{level + 1}"
            )
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    if can_claim:
        builder.row(
            types.InlineKeyboardButton(
                text="✅ Забрать",
                callback_data=f"pass:claim:{level}"
            )
        )

    builder.row(
        types.InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="pass:menu"
        )
    )

    return builder.as_markup()


def get_bonus_kb(can_claim: bool = True):
    builder = InlineKeyboardBuilder()

    if can_claim:
        builder.row(
            types.InlineKeyboardButton(
                text="🎁 Забрать бонус",
                callback_data="pass:bonus_claim"
            )
        )

    builder.row(
        types.InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="pass:menu"
        )
    )

    return builder.as_markup()


def get_tasks_kb(tasks: list):
    builder = InlineKeyboardBuilder()

    for task in tasks:
        if task.get("is_completed") and not task.get("claimed"):
            builder.row(
                types.InlineKeyboardButton(
                    text=f"✅ Забрать {task['reward']} 🍑",
                    callback_data=f"pass:task_claim:{task['id']}"
                )
            )

    builder.row(
        types.InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="pass:menu"
        )
    )
    return builder.as_markup()


async def safe_edit_or_send_photo(message_obj: types.Message, text: str, reply_markup):
    if message_obj.photo:
        try:
            await message_obj.edit_caption(
                caption=text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
            return
        except TelegramBadRequest:
            pass

    try:
        await message_obj.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    except TelegramBadRequest:
        await message_obj.answer_photo(
            photo=PHOTO_URL,
            caption=text,
            parse_mode="HTML",
            reply_markup=reply_markup
        )


async def render_pass_menu(target_message: types.Message, user_id: int):
    pass_user = await get_pass_user(user_id)
    peaches = int(pass_user.get("peaches", 0))
    is_ultra = bool(pass_user.get("is_ultra", False))
    user_level = get_user_level(peaches)
    days_left = get_days_left()

    text = build_main_menu_text(
        user_level=user_level,
        is_ultra=is_ultra,
        days_left=days_left
    )

    await safe_edit_or_send_photo(
        message_obj=target_message,
        text=text,
        reply_markup=get_main_pass_kb()
    )


@router.message(Command("pass"))
async def cmd_pass(message: types.Message):
    pass_user = await get_pass_user(message.from_user.id)
    peaches = int(pass_user.get("peaches", 0))
    is_ultra = bool(pass_user.get("is_ultra", False))
    user_level = get_user_level(peaches)
    days_left = get_days_left()

    text = build_main_menu_text(
        user_level=user_level,
        is_ultra=is_ultra,
        days_left=days_left
    )

    await message.answer_photo(
        photo=PHOTO_URL,
        caption=text,
        parse_mode="HTML",
        reply_markup=get_main_pass_kb()
    )


@router.callback_query(F.data == "pass:menu")
async def cb_pass_menu(callback: types.CallbackQuery):
    await render_pass_menu(callback.message, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data.startswith("pass:stages:"))
async def cb_pass_stages(callback: types.CallbackQuery):
    level = int(callback.data.split(":")[2])

    pass_user = await get_pass_user(callback.from_user.id)
    claimed_levels = await get_claimed_levels(callback.from_user.id)

    peaches = int(pass_user.get("peaches", 0))
    text = build_stage_text(level, peaches, claimed_levels)

    can_claim = (
        peaches >= get_level_required_peaches(level)
        and level not in claimed_levels
    )

    kb = get_stage_kb(level=level, can_claim=can_claim)

    await safe_edit_or_send_photo(
        message_obj=callback.message,
        text=text,
        reply_markup=kb
    )

    await callback.answer()


@router.callback_query(F.data == "pass:tasks")
async def cb_pass_tasks(callback: types.CallbackQuery):
    tasks = await get_or_create_today_tasks(callback.from_user.id)
    text = build_tasks_text(tasks, get_hours_left_until_reset())

    await safe_edit_or_send_photo(
        message_obj=callback.message,
        text=text,
        reply_markup=get_tasks_kb(tasks)
    )

    await callback.answer()


@router.callback_query(F.data.startswith("pass:task_claim:"))
async def cb_pass_task_claim(callback: types.CallbackQuery):
    task_row_id = int(callback.data.split(":")[2])

    success, result = await claim_task_reward(callback.from_user.id, task_row_id)

    if not success:
        return await callback.answer(str(result), show_alert=True)

    tasks = await get_or_create_today_tasks(callback.from_user.id)
    text = (
        "✅ <b>Награда за задание получена!</b>\n\n"
        f"Теперь у тебя: <b>{result}</b> 🍑\n\n"
    )
    text += build_tasks_text(tasks, get_hours_left_until_reset())

    await safe_edit_or_send_photo(
        message_obj=callback.message,
        text=text,
        reply_markup=get_tasks_kb(tasks)
    )
    await callback.answer("Награда получена!")


@router.callback_query(F.data == "pass:bonus")
async def cb_pass_bonus(callback: types.CallbackQuery):
    already_claimed = await has_claimed_daily_bonus(callback.from_user.id)
    text = build_bonus_text(already_claimed=already_claimed)

    await safe_edit_or_send_photo(
        message_obj=callback.message,
        text=text,
        reply_markup=get_bonus_kb(can_claim=not already_claimed)
    )

    await callback.answer()


@router.callback_query(F.data == "pass:bonus_claim")
async def cb_pass_bonus_claim(callback: types.CallbackQuery):
    success, new_peaches = await claim_daily_bonus(callback.from_user.id)

    if success:
        text = (
            "✅ <b>Бонус получен!</b>\n\n"
            "Ты забрал ежедневный бонус: 50 🍑\n"
            f"Теперь у тебя: <b>{new_peaches}</b> 🍑"
        )
        alert_text = "Бонус получен!"
    else:
        text = (
            "⌛️ <b>Ежедневный бонус</b>\n\n"
            "Ты уже забрал бонус сегодня."
        )
        alert_text = "Ты уже получал бонус сегодня"

    await safe_edit_or_send_photo(
        message_obj=callback.message,
        text=text,
        reply_markup=get_back_kb()
    )

    await callback.answer(alert_text)


@router.callback_query(F.data == "pass:buy_ultra")
async def cb_pass_buy_ultra(callback: types.CallbackQuery):
    text = (
        "🔥 <b>Ультра пропуск</b>\n\n"
        "Покупка Ультра пропуска скоро будет доступна."
    )

    await safe_edit_or_send_photo(
        message_obj=callback.message,
        text=text,
        reply_markup=get_back_kb()
    )

    await callback.answer()


@router.callback_query(F.data == "pass:info")
async def cb_pass_info(callback: types.CallbackQuery):
    text = build_info_text()

    await safe_edit_or_send_photo(
        message_obj=callback.message,
        text=text,
        reply_markup=get_back_kb()
    )

    await callback.answer()


@router.callback_query(F.data.startswith("pass:claim:"))
async def cb_pass_claim(callback: types.CallbackQuery, get_user, save_db):
    level = int(callback.data.split(":")[2])

    pass_user = await get_pass_user(callback.from_user.id)
    claimed_levels = await get_claimed_levels(callback.from_user.id)
    peaches = int(pass_user.get("peaches", 0))

    if level in claimed_levels:
        return await callback.answer("Награда уже получена", show_alert=True)

    if peaches < get_level_required_peaches(level):
        return await callback.answer("Ты ещё не достиг этого уровня", show_alert=True)

    from .pass_data import PASS_LEVELS
    rewards = PASS_LEVELS[level]["rewards"]

    user = await get_user(callback.from_user.id, callback.from_user.username)
    if not user:
        return await callback.answer("Ошибка загрузки профиля", show_alert=True)

    inv = user.get("inventory")
    if not isinstance(inv, dict):
        if isinstance(inv, list):
            new_inv = {}
            for item in inv:
                new_inv[item] = new_inv.get(item, 0) + 1
            user["inventory"] = new_inv
            inv = new_inv
        else:
            user["inventory"] = {}
            inv = user["inventory"]

    for emoji, amount in rewards.items():
        inv[emoji] = inv.get(emoji, 0) + amount

    await save_db(callback.from_user.id, user)

    from .pass_db import claim_level
    await claim_level(callback.from_user.id, level)

    text = (
        f"✅ <b>Награда за уровень {level} получена!</b>\n\n"
        "Все предметы уже добавлены в твой инвентарь."
    )

    await safe_edit_or_send_photo(
        message_obj=callback.message,
        text=text,
        reply_markup=get_back_kb()
    )

    await callback.answer("Награда получена!")


ALLOWED_CHAT_ID = -1003858938513


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







