from aiogram import Router, types
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.utils.deep_linking import create_start_link
from items import GAME_ITEMS

router = Router()

# Настройки
REWARD_COINS = 1000
FARMCOIN_EMOJI = "💰"
REFERRALS_FOR_KING = 20

# Берем эмодзи из GAME_ITEMS
KING_ITEM_EMOJI = "👑"  # По умолчанию, если в GAME_ITEMS нет


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
    user = get_user(user_id, message.from_user.username)
    args = command.args

    # Проверка регистрации
    if user.get("registered"):
        return await message.answer("С возвращением! 👋")

    user["registered"] = True

    # Сначала сохраняем самого юзера
    save_db(user_id, user)

    # Если есть реферальный код
    if args and args.isdigit():
        inviter_id = int(args)

        if inviter_id == user_id:
            return await message.answer("Добро пожаловать! (Нельзя приглашать самого себя)")

        inviter = get_user(inviter_id)
        if inviter:
            inviter_inv = ensure_inv_dict(inviter)

            # 1. Начисляем монеты в инвентарь пригласившего
            inviter_inv[FARMCOIN_EMOJI] = inviter_inv.get(FARMCOIN_EMOJI, 0) + REWARD_COINS

            # 2. Счетчик рефералов
            inviter["referral_count"] = inviter.get("referral_count", 0) + 1
            current_refs = inviter["referral_count"]

            # 3. Бонус за 20 рефералов
            custom_msg = ""
            if current_refs == REFERRALS_FOR_KING:
                inviter_inv[KING_ITEM_EMOJI] = inviter_inv.get(KING_ITEM_EMOJI, 0) + 1
                inviter["custom_role"] = "👑 Реферальный король"
                custom_msg = f"\n\n👑 <b>Король!</b> Ты пригласил {REFERRALS_FOR_KING} друзей и получил <b>{KING_ITEM_EMOJI}</b>!"

            # --- SQLITE FIX (Сохраняем пригласившего) ---
            save_db(inviter_id, inviter)

            await message.answer("✅ Ты успешно зарегистрировался по ссылке друга!")

            try:
                await message.bot.send_message(
                    inviter_id,
                    f"🎉 По твоей ссылке зашел новый друг! Тебе начислено <b>{REWARD_COINS} {FARMCOIN_EMOJI}</b> в инвентарь.{custom_msg}",
                    parse_mode="HTML"
                )
            except:
                pass
    else:
        await message.answer("Добро пожаловать в бота! Используй /ref, чтобы приглашать друзей.")


@router.message(Command("ref"))
async def cmd_ref(message: types.Message, get_user):
    user = get_user(message.from_user.id)
    ref_count = user.get("referral_count", 0)

    # Генерируем ссылку
    link = await create_start_link(message.bot, str(message.from_user.id), encode=False)

    text = (
        f"🔗 <b>Твоя реферальная ссылка:</b>\n"
        f"<code>{link}</code>\n\n"
        f"💰 За каждого друга ты получишь: <b>{REWARD_COINS} {FARMCOIN_EMOJI}</b> (в инвентарь)\n"
        f"👥 Приглашено: <b>{ref_count}</b>\n\n"
        f"🎁 <b>Бонус:</b> {REFERRALS_FOR_KING} друзей = предмет <b>{KING_ITEM_EMOJI}</b>!"
    )

    if ref_count >= REFERRALS_FOR_KING:
        text += f"\n\n👑 Статус <b>Короля</b> получен!"

    await message.answer(text, parse_mode="HTML")
