from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ivent.pass_data import PASS_IMAGE_URL
from ivent.pass_texts import build_main_menu_text, build_info_text
from ivent.pass_utils import get_days_left, build_stage_text, get_hours_left_until_reset

router = Router()


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

    if level < 10:
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


def get_tasks_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="pass:menu"
        )
    )
    return builder.as_markup()


@router.message(Command("pass"))
async def cmd_pass(message: types.Message):
    # Пока временные тестовые данные
    user_level = 0
    is_ultra = False
    days_left = get_days_left()

    text = build_main_menu_text(
        user_level=user_level,
        is_ultra=is_ultra,
        days_left=days_left
    )

    if PASS_IMAGE_URL:
        await message.answer_photo(
            photo=PASS_IMAGE_URL,
            caption=text,
            parse_mode="HTML",
            reply_markup=get_main_pass_kb()
        )
    else:
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=get_main_pass_kb()
        )


@router.callback_query(F.data == "pass:menu")
async def cb_pass_menu(callback: types.CallbackQuery):
    user_level = 0
    is_ultra = False
    days_left = get_days_left()

    text = build_main_menu_text(
        user_level=user_level,
        is_ultra=is_ultra,
        days_left=days_left
    )

    if callback.message.photo:
        await callback.message.edit_caption(
            caption=text,
            parse_mode="HTML",
            reply_markup=get_main_pass_kb()
        )
    else:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_main_pass_kb()
        )

    await callback.answer()


@router.callback_query(F.data.startswith("pass:stages:"))
async def cb_pass_stages(callback: types.CallbackQuery):
    level = int(callback.data.split(":")[2])

    # Пока тест
    peaches = 0
    claimed_levels = []

    text = build_stage_text(level, peaches, claimed_levels)

    # can_claim пока выключен
    kb = get_stage_kb(level=level, can_claim=False)

    if callback.message.photo:
        await callback.message.edit_caption(
            caption=text,
            parse_mode="HTML",
            reply_markup=kb
        )
    else:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=kb
        )

    await callback.answer()


@router.callback_query(F.data == "pass:tasks")
async def cb_pass_tasks(callback: types.CallbackQuery):
    # Временные тестовые задания
    tasks = [
        {
            "text": "Написать в чат 50 сообщений",
            "progress": 0,
            "target": 50,
            "reward": 200,
            "is_completed": False
        },
        {
            "text": "Подрочить 250 раз",
            "progress": 0,
            "target": 250,
            "reward": 60,
            "is_completed": False
        },
        {
            "text": "Сыграть в /dice 1 раз",
            "progress": 0,
            "target": 1,
            "reward": 10,
            "is_completed": False
        }
    ]

    from ivent.pass_texts import build_tasks_text
    text = build_tasks_text(tasks, get_hours_left_until_reset())

    if callback.message.photo:
        await callback.message.edit_caption(
            caption=text,
            parse_mode="HTML",
            reply_markup=get_tasks_kb()
        )
    else:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_tasks_kb()
        )

    await callback.answer()


@router.callback_query(F.data == "pass:bonus")
async def cb_pass_bonus(callback: types.CallbackQuery):
    from ivent.pass_texts import build_bonus_text
    text = build_bonus_text(already_claimed=False)

    if callback.message.photo:
        await callback.message.edit_caption(
            caption=text,
            parse_mode="HTML",
            reply_markup=get_bonus_kb(can_claim=True)
        )
    else:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_bonus_kb(can_claim=True)
        )

    await callback.answer()


@router.callback_query(F.data == "pass:bonus_claim")
async def cb_pass_bonus_claim(callback: types.CallbackQuery):
    from ivent.pass_texts import build_bonus_text
    text = (
        "✅ <b>Бонус получен!</b>\n\n"
        "Ты забрал ежедневный бонус: 50 🍑"
    )

    if callback.message.photo:
        await callback.message.edit_caption(
            caption=text,
            parse_mode="HTML",
            reply_markup=get_back_kb()
        )
    else:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_back_kb()
        )

    await callback.answer("Бонус получен!")


@router.callback_query(F.data == "pass:buy_ultra")
async def cb_pass_buy_ultra(callback: types.CallbackQuery):
    text = (
        "🔥 <b>Ультра пропуск</b>\n\n"
        "Покупка Ультра пропуска скоро будет доступна."
    )

    if callback.message.photo:
        await callback.message.edit_caption(
            caption=text,
            parse_mode="HTML",
            reply_markup=get_back_kb()
        )
    else:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_back_kb()
        )

    await callback.answer()


@router.callback_query(F.data == "pass:info")
async def cb_pass_info(callback: types.CallbackQuery):
    text = build_info_text()

    if callback.message.photo:
        await callback.message.edit_caption(
            caption=text,
            parse_mode="HTML",
            reply_markup=get_back_kb()
        )
    else:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_back_kb()
        )

    await callback.answer()


@router.callback_query(F.data.startswith("pass:claim:"))
async def cb_pass_claim(callback: types.CallbackQuery):
    level = int(callback.data.split(":")[2])

    text = (
        f"✅ <b>Тестовый режим</b>\n\n"
        f"Награда за уровень {level} позже будет подключена через Supabase."
    )

    if callback.message.photo:
        await callback.message.edit_caption(
            caption=text,
            parse_mode="HTML",
            reply_markup=get_back_kb()
        )
    else:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_back_kb()
        )

    await callback.answer()
