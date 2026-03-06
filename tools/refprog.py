from aiogram import Router, types
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.utils.deep_linking import create_start_link
from items import GAME_ITEMS  # Импортируем твои предметы

router = Router()

# Настраиваем награды (монеты и предмет для короля)
REWARD_COINS = 1000  # Сколько ФармКоинов давать за приглашение
FARMCOIN_EMOJI = "💰"  # Эмодзи валюты (как в твоем инвентаре)
REFERRALS_FOR_KING = 20  # Количество рефералов для статуса "Король"

# Берем эмодзи из GAME_ITEMS (если ключа нет, ставим 👑 по умолчанию)
KING_ITEM_EMOJI = GAME_ITEMS.get("👑", {}).get("emoji", "👑")


def ensure_inv_dict(user) -> dict:
    inv = user.get("inventory")
    if not isinstance(inv, dict):
        inv = {}
        user["inventory"] = inv
    return inv


@router.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject, get_user, save_db):
    user_id = message.from_user.id
    user = get_user(user_id)
    args = command.args

    # Проверка, новый ли юзер
    if user.get("registered"):
        return await message.answer("С возвращением!")

    user["registered"] = True
    save_db()

    # Если есть код пригласившего
    if args and args.isdigit():
        inviter_id = int(args)

        if inviter_id == user_id:
            await message.answer("Добро пожаловать! (Нельзя переходить по своей же ссылке)")
        else:
            inviter = get_user(inviter_id)
            inviter_inv = ensure_inv_dict(inviter)

            # 1. Начисляем ФармКоины прямо в ИНВЕНТАРЬ
            current_coins = inviter_inv.get(FARMCOIN_EMOJI, 0)
            inviter_inv[FARMCOIN_EMOJI] = current_coins + REWARD_COINS

            # 2. Увеличиваем счетчик рефералов
            inviter["referral_count"] = inviter.get("referral_count", 0) + 1
            current_refs = inviter["referral_count"]

            # 3. Выдаем предмет-корону за 20 рефов
            custom_msg = ""
            if current_refs == REFERRALS_FOR_KING:
                # Даем 1 корону в инвентарь, используя эмодзи из GAME_ITEMS
                current_crowns = inviter_inv.get(KING_ITEM_EMOJI, 0)
                inviter_inv[KING_ITEM_EMOJI] = current_crowns + 1

                inviter["custom_role"] = "👑 Реферальный король"  # Оставляем и текстовую роль на всякий случай
                custom_msg = f"\n\n👑 <b>Поздравляем!</b> Ты пригласил {REFERRALS_FOR_KING} друзей! В твой инвентарь добавлен уникальный предмет <b>Корона Короля ({KING_ITEM_EMOJI})</b>!"

            save_db()

            await message.answer("Вы успешно зарегистрировались по ссылке друга!")

            # Пишем пригласившему
            try:
                await message.bot.send_message(
                    inviter_id,
                    f"🎉 По твоей ссылке зарегистрировался новый друг! В твой инвентарь добавлено <b>{REWARD_COINS} {FARMCOIN_EMOJI}</b>.{custom_msg}",
                    parse_mode="HTML"
                )
            except Exception:
                pass
    else:
        await message.answer("Добро пожаловать в бота!")


@router.message(Command("ref"))
async def cmd_ref(message: types.Message, get_user):
    user = get_user(message.from_user.id)
    ref_count = user.get("referral_count", 0)

    link = await create_start_link(message.bot, str(message.from_user.id), encode=False)

    text = (
        f"🔗 <b>Твоя реферальная ссылка:</b>\n"
        f"<code>{link}</code>\n\n"
        f"💰 За каждого приглашенного друга ты получишь <b>{REWARD_COINS} {FARMCOIN_EMOJI}</b> прямо в инвентарь.\n"
        f"👥 Приглашено друзей: <b>{ref_count}</b>\n\n"
        f"🎁 <b>Бонус:</b> Пригласи {REFERRALS_FOR_KING} друзей, чтобы получить предмет <b>{KING_ITEM_EMOJI}</b> в инвентарь!"
    )

    if ref_count >= REFERRALS_FOR_KING:
        text += f"\n\n👑 Статус короля получен! Предмет <b>{KING_ITEM_EMOJI}</b> уже в инвентаре."

    await message.answer(text, parse_mode="HTML")