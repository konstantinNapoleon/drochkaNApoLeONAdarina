from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from aiogram.utils.deep_linking import create_start_link
from items import GAME_ITEMS

router = Router()

# Настройки
REWARD_COINS = 1000
FARMCOIN_EMOJI = "💰"
REFERRALS_FOR_KING = 20
CROWN_EMOJI = "👑"


# --- ДОБАВЬ ЭТОТ ТЕКСТ В НАЧАЛО ФАЙЛА ---
WELCOME_TEXT = (
  "👋 Добро пожаловать в @droch_bot\n\n"
  "🔥 Заходи каждый день — получай бонусы. По команде /dailybonus@droch_bot\n\n"
  "🔥 Участвуй в ивентах — забирай эксклюзивы.\n\n"
  "📰 А так же у нас есть канал с новостями где ты можешь получить бонус коды для прокачки своего аккаунта: https://t.me/droch_information\n\n"
  "🤔 Хочешь обменяться валютой с другим участником бота? Отличное решение! Для этого у нас есть официальный чат: https://t.me/official_chat_droch"
)


def ensure_inv_dict(user) -> dict:
    inv = user.get("inventory")
    if not isinstance(inv, dict):
        if isinstance(inv, list):
            new_inv = {}
            for item in inv:
                new_inv[item] = new_inv.get(item, 0) + 1
            user["inventory"] = new_inv
        else:
            user["inventory"] = {}
    return user["inventory"]


@router.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject, get_user, save_db):
    user_id = message.from_user.id
    # Получаем данные пользователя из базы
    user = await get_user(user_id, message.from_user.username)
    args = command.args

    # --- ПРОВЕРКА: ЕСЛИ ПОЛЬЗОВАТЕЛЬ УЖЕ ЕСТЬ В БОТЕ ---
    if user.get("registered"):
        # Если он уже был в боте, реф-ссылка игнорируется
        # Мы просто отправляем ему приветственный текст и выходим из функции
        return await message.answer(WELCOME_TEXT, disable_web_page_preview=True)

    # --- ЛОГИКА ДЛЯ НОВОГО ПОЛЬЗОВАТЕЛЯ (РЕГИСТРАЦИЯ) ---
    user["registered"] = True
    ref_msg = ""

    # Проверяем, пришел ли он по реферальной ссылке
    if args and args.isdigit():
        inviter_id = int(args)

        # Не даем приглашать самого себя
        if inviter_id != user_id:
            inviter = await get_user(inviter_id)

            # Если пригласитель существует в базе
            if inviter:
                # Начисляем монеты пригласителю
                inv_dict = ensure_inv_dict(inviter)
                inv_dict[FARMCOIN_EMOJI] = inv_dict.get(FARMCOIN_EMOJI, 0) + REWARD_COINS
                inviter["referral_count"] = inviter.get("referral_count", 0) + 1

                # Проверка на достижение лимита для Короны
                custom_msg = ""
                if inviter.get("referral_count", 0) >= REFERRALS_FOR_KING and not inviter.get("king_reward_claimed"):
                    inv_dict[CROWN_EMOJI] = inv_dict.get(CROWN_EMOJI, 0) + 1
                    inviter["king_reward_claimed"] = True
                    inviter["custom_role"] = "👑 Реферальный король"
                    custom_msg = f"\n\n👑 <b>УРА!</b> Ты пригласил {REFERRALS_FOR_KING} друзей и получил <b>Корону ({CROWN_EMOJI})</b>!"

                # Сохраняем данные пригласителя
                await save_db(inviter_id, inviter)
                ref_msg = "🎉 Вы зарегистрировались по ссылке друга!\n\n"

                # Уведомляем пригласителя
                try:
                    await message.bot.send_message(
                        inviter_id,
                        f"🔔 Новый реферал! Зачислено: <b>{REWARD_COINS} {FARMCOIN_EMOJI}</b>.{custom_msg}",
                        parse_mode="HTML"
                    )
                except:
                    pass

    # Сохраняем нового пользователя как "зарегистрированного"
    await save_db(user_id, user)

    # Отправляем финальный текст
    await message.answer(f"{ref_msg}{WELCOME_TEXT}", disable_web_page_preview=True)


@router.message(Command("ref"))
async def cmd_ref(message: types.Message, get_user, save_db):
    user = await get_user(message.from_user.id, message.from_user.username)
    ref_count = user.get("referral_count", 0)

    # --- ПРОВЕРКА НА ВЫДАЧУ КОРОНЫ ПРЯМО ЗДЕСЬ ---
    if ref_count >= REFERRALS_FOR_KING and not user.get("king_reward_claimed"):
        inv = ensure_inv_dict(user)
        inv[CROWN_EMOJI] = inv.get(CROWN_EMOJI, 0) + 1
        user["king_reward_claimed"] = True
        user["custom_role"] = "👑 Реферальный король"
        await save_db(message.from_user.id, user)
        await message.answer(
            f"🎊 <b>Поздравляем!</b> Ты уже пригласил {ref_count} друзей, поэтому мы выдали тебе <b>Корону ({CROWN_EMOJI})</b> прямо сейчас!",
            parse_mode="HTML")

    link = await create_start_link(message.bot, str(message.from_user.id), encode=False)
    text = (
        f"🔗 <b>Твоя реферальная ссылка:</b>\n<code>{link}</code>\n\n"
        f"💰 Награда: <b>{REWARD_COINS} {FARMCOIN_EMOJI}</b> за друга.\n"
        f"👥 Приглашено: <b>{ref_count}</b>\n\n"
        f"🎁 <b>Цель:</b> {REFERRALS_FOR_KING} друзей для получения <b>Короны ({CROWN_EMOJI})</b>."
    )

    if user.get("king_reward_claimed"):
        text += f"\n\n👑 <b>Статус:</b> Реферальный король. Предмет в инвентаре!"

    await message.answer(text, parse_mode="HTML")
