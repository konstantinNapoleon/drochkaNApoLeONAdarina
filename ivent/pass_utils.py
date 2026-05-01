import math
import datetime

from ivent.pass_data import PEACHES_PER_LEVEL, MAX_LEVEL, PASS_LEVELS, SEASON_END
from items import GAME_ITEMS


def get_user_level(peaches: int) -> int:
    if peaches <= 0:
        return 0
    return min(MAX_LEVEL, peaches // PEACHES_PER_LEVEL)


def get_level_required_peaches(level: int) -> int:
    return level * PEACHES_PER_LEVEL


def get_level_progress(peaches: int, level: int):
    """
    Возвращает прогресс внутри конкретного уровня.
    Например:
    level=4 -> диапазон 451-600 при шаге 150
    """
    if level <= 1:
        prev_required = 0
    else:
        prev_required = (level - 1) * PEACHES_PER_LEVEL

    current_required = level * PEACHES_PER_LEVEL
    current_progress = max(0, peaches - prev_required)
    need_for_level = current_required - prev_required

    if current_progress > need_for_level:
        current_progress = need_for_level

    return current_progress, need_for_level


def build_progress_bar(current: int, total: int, size: int = 10) -> str:
    if total <= 0:
        return "▱" * size

    filled = math.floor((current / total) * size)
    if filled > size:
        filled = size

    return "▰" * filled + "▱" * (size - filled)


def format_rewards(rewards: dict) -> str:
    lines = []

    for emoji, amount in rewards.items():
        item_data = GAME_ITEMS.get(emoji, {})
        item_name = item_data.get("name", "Неизвестный предмет")

        if amount == 1:
            lines.append(f"{emoji} <b>{item_name}</b>")
        else:
            lines.append(f"{emoji} <b>{item_name}</b> x{amount}")

    return "\n".join(lines)


def get_level_status(peaches: int, level: int, claimed_data: dict, is_ultra: bool) -> str:
    required = get_level_required_peaches(level)
    level_claims = claimed_data.get(str(level), {})  # Получаем статусы для этого уровня

    # Проверяем, есть ли что забирать
    can_claim_regular = not level_claims.get("regular", False)
    can_claim_ultra = is_ultra and not level_claims.get("ultra", False)

    level_data = PASS_LEVELS[level]
    has_ultra_reward = "ultra_rewards" in level_data and level_data["ultra_rewards"]

    if peaches >= required:
        if can_claim_regular or (can_claim_ultra and has_ultra_reward):
            return "ожидает сбор"
        else:
            return "получено ✅"
    else:
        return "не достигнуто"


def get_days_left() -> int:
    now = datetime.datetime.now()
    delta = SEASON_END - now
    return max(0, delta.days)


def get_hours_left_until_reset() -> str:
    now = datetime.datetime.now()
    tomorrow = now + datetime.timedelta(days=1)
    next_reset = datetime.datetime(
        tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0
    )
    delta = next_reset - now
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    return f"{hours}ч {minutes}м"


def build_stage_text(level: int, peaches: int, claimed_levels: dict, is_ultra: bool) -> str:
    level_data = PASS_LEVELS[level]
    level_claims = claimed_levels.get(str(level), {})  # Уровни в JSON могут быть строками

    # 1. Форматируем награды с галочками
    all_rewards_lines = []

    # Обычные награды
    regular_rewards = level_data.get("rewards", {})
    if regular_rewards:
        claimed_status = "✅" if level_claims.get("regular") else "❌"
        formatted_lines = format_rewards(regular_rewards).split('\n')
        for line in formatted_lines:
            all_rewards_lines.append(f"{line} [{claimed_status}]")

    # Ультра-награды
    ultra_rewards = level_data.get("ultra_rewards", {})
    if ultra_rewards:
        claimed_status = "✅" if level_claims.get("ultra") else "❌"

        for emoji, amount in ultra_rewards.items():
            item_data = GAME_ITEMS.get(emoji, {})
            item_name = item_data.get("name", "Неизвестный предмет")

            base_line = f"{emoji} <b>{item_name}</b>"
            if amount > 1:
                base_line += f" x{amount}"

            if not is_ultra:
                all_rewards_lines.append(f"🔒 {base_line} [{claimed_status}]")
            else:
                all_rewards_lines.append(f"{base_line} [{claimed_status}]")

    rewards_text = "\n".join(all_rewards_lines)

    # 2. Получаем статус и прогресс
    status = get_level_status(peaches, level, claimed_levels, is_ultra)
    current, total = get_level_progress(peaches, level)
    bar = build_progress_bar(current, total)

    return (
        f"📦 <b>Боевой Пропуск | Уровень {level}</b>\n\n"
        f"<b>Награда:</b>\n"
        f"{rewards_text}\n\n"
        f"Прогресс: {bar} {current}/{total}\n\n"
        f"Статус: <b>{status}</b>"
    )
