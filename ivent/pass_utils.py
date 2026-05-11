import math
import datetime

# --- ОБНОВЛЕННЫЕ ИМПОРТЫ ---
from .pass_data import (
    CHERRIES_PER_LEVEL,
    MAX_LEVEL,
    PASS_LEVELS,
    SEASON_END,
    SECTORS,
    # Добавляем константы уровней пропуска для логики
    PASS_TIER_NORMAL,
    PASS_TIER_MEGA
)
from items import GAME_ITEMS
from handlers.bafus import ACHIEVEMENTS_LIST


# --- Твои функции (без изменений) ---
def get_sector_status(user_level: int, sector_id: str) -> str:
    sector_data = SECTORS[sector_id]
    if user_level < sector_data['unlocks_at']:
        return "🔒"
    max_level_in_sector = max(sector_data['levels'])
    if user_level > max_level_in_sector:
        return "✅"
    return "❌"


def get_current_sector(level: int) -> tuple[str, str]:
    for sector_id, sector_data in SECTORS.items():
        if level in sector_data['levels']:
            return sector_id, sector_data['name']
    return "?", "Неизвестный"


def get_user_level(cherries: int) -> int:
    if cherries <= 0:
        return 0
    return min(MAX_LEVEL, cherries // CHERRIES_PER_LEVEL)


def get_level_required_cherries(level: int) -> int:
    return level * CHERRIES_PER_LEVEL


def get_level_progress(cherries: int, level: int):
    if level <= 1:
        prev_required = 0
    else:
        prev_required = (level - 1) * CHERRIES_PER_LEVEL
    current_required = level * CHERRIES_PER_LEVEL
    current_progress = max(0, cherries - prev_required)
    need_for_level = current_required - prev_required
    if current_progress > need_for_level:
        current_progress = need_for_level
    return current_progress, need_for_level


def build_progress_bar(current: int, total: int, size: int = 10) -> str:
    if total <= 0:
        return "▱" * size
    filled = math.floor((current / total) * size)
    return "▰" * min(filled, size) + "▱" * (size - min(filled, size))


def format_rewards(rewards: dict) -> str:
    lines = []
    for emoji, amount in rewards.items():
        item_data = GAME_ITEMS.get(emoji, {})
        item_name = item_data.get("name", "Неизвестный предмет")
        lines.append(f"{emoji} <b>{item_name}</b>" + (f" x{amount}" if amount > 1 else ""))
    return "\n".join(lines)


def get_days_left() -> int:
    delta = SEASON_END - datetime.datetime.now()
    return max(0, delta.days)


def get_hours_left_until_reset() -> str:
    now = datetime.datetime.now()
    next_reset = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    delta = next_reset - now
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    return f"{hours}ч {minutes}м"


# --- ИЗМЕНЕННЫЕ ФУНКЦИИ ---

def get_level_status(cherries: int, level: int, claimed_data: dict, pass_tier: int) -> str:
    """Изменено: Принимает pass_tier вместо is_ultra."""
    required = get_level_required_cherries(level)
    if cherries < required:
        return "не достигнуто"

    level_claims = claimed_data.get(str(level), {})
    level_data = PASS_LEVELS[level]

    can_claim_regular = not level_claims.get("regular", False)
    has_ultra_reward = "ultra_rewards" in level_data and level_data["ultra_rewards"]

    # Ультра и Мега могут забирать Ультра-награды
    can_claim_ultra = pass_tier > PASS_TIER_NORMAL and has_ultra_reward and not level_claims.get("ultra", False)

    if can_claim_regular or can_claim_ultra:
        return "ожидает сбор"
    else:
        return "получено ✅"


def build_stage_text(level: int, cherries: int, claimed_levels: dict, pass_tier: int) -> str:
    """Полностью переписан для поддержки 3-х уровней пропуска и бонусных уровней."""

    # --- Новая проверка для бонусных уровней ---
    # Если уровень больше 40 и у игрока нет Мега пропуска, показываем заглушку
    if level > 40 and pass_tier < PASS_TIER_MEGA:
        return (
            f"📦 <b>Бонусный Этап {level}</b>\n\n"
            "Этот этап и его награды доступны только владельцам <b>💎 Мега пропуска</b>."
        )

    level_data = PASS_LEVELS.get(level)
    if not level_data:
        return f"Ошибка: Данные для этапа {level} не найдены."

    level_claims = claimed_levels.get(str(level), {})
    all_rewards_lines = []

    # Обычные награды (и награды бонусных уровней для Мега)
    regular_rewards = level_data.get("rewards", {})
    if regular_rewards:
        status = "✅" if level_claims.get("regular") else "❌"
        formatted_lines = format_rewards(regular_rewards).split('\n')
        all_rewards_lines.extend(f"{line} [{status}]" for line in formatted_lines)

    # Ультра-награды
    ultra_rewards = level_data.get("ultra_rewards", {})
    if ultra_rewards:
        status = "✅" if level_claims.get("ultra") else "❌"
        formatted_lines = format_rewards(ultra_rewards).split('\n')
        # Показываем замок только для обычного пропуска
        if pass_tier == PASS_TIER_NORMAL:
            all_rewards_lines.extend(f"🔒 {line} [{status}]" for line in formatted_lines)
        else:
            all_rewards_lines.extend(f"{line} [{status}]" for line in formatted_lines)

    rewards_text = "\n".join(all_rewards_lines)

    # Блок ачивки (без изменений)
    achievement_text = ""
    if "achievement" in level_data:
        ach_id = level_data["achievement"]
        ach_info = ACHIEVEMENTS_LIST.get(ach_id)
        if ach_info:
            status = "✅" if level_claims.get("regular") else "❌"
            achievement_text = f"\n\nАчивка: {ach_info['emoji']} | {ach_info['name']} [{status}]"

    # Передаем pass_tier в get_level_status
    status = get_level_status(cherries, level, claimed_levels, pass_tier)
    current, total = get_level_progress(cherries, level)
    bar = build_progress_bar(current, total)

    sector_id, _ = get_current_sector(level)
    sector_title = f"(Сектор {sector_id})" if sector_id != "?" else "(Бонусный этап)"

    return (
        f"📦 <b>Боевой Пропуск | Этап {level} {sector_title}</b>\n\n"
        f"<b>Награда:</b>\n{rewards_text}"
        f"{achievement_text}\n\n"
        f"Прогресс: {bar} {current}/{total}\n\n"
        f"Статус: <b>{status}</b>"
    )




