
# pass_texts.py

# --- ОБНОВЛЕННЫЕ ИМПОРТЫ ---
from .pass_data import (
  SEASON_TITLE,
  SEASON_DESCRIPTION,
  # Константы для всех уровней пропуска
  PASS_TIER_ULTRA, PASS_TIER_MEGA,
  # Стоимости
  ULTRA_PASS_COST, MEGA_PASS_COST,
  # Бонусы
  DAILY_BONUS_REWARD, ULTRA_PASS_DAILY_BONUS, MEGA_PASS_DAILY_BONUS,
  # Задания
  DAILY_TASKS_COUNT, MEGA_PASS_TASKS_COUNT,
  # Прочее
  SECTORS,
  MAX_LEVEL,
  CHERRIES_PER_LEVEL,
  CHERRY_EMOJI,
  CHERRY_TO_FRAG_RATE
)

# --- Твоя функция определения сектора (без изменений) ---
def get_sector_name(user_level: int) -> str:
  for sector_id in sorted(SECTORS.keys(), reverse=True):
    sector_data = SECTORS[sector_id]
    if user_level >= sector_data['unlocks_at']:
      return f"{sector_id}: {sector_data['name']}"
  return "Неизвестно"


# --- ОБНОВЛЕННЫЕ ФУНКЦИИ ГЕНЕРАЦИИ ТЕКСТА ---

def build_main_menu_text(user_level: int, pass_tier: int, days_left: int) -> str:
  """Изменено: Отображает правильный тип пропуска (Обычный, Ультра, Мега)."""
  if pass_tier == PASS_TIER_MEGA:
    pass_type = "💎 Мега"
  elif pass_tier == PASS_TIER_ULTRA:
    pass_type = "💠 Ультра"
  else:
    pass_type = "Обычный"

  sector_name = get_sector_name(user_level)

  return (
    f"<b>{SEASON_TITLE}</b>\n\n"
    f"— Твой этап: {user_level}\n"
    f"— Твоя Секта: {sector_name}\n"
    f"— Пропуск: {pass_type}\n"
    f"— До окончания: {days_left} д.\n\n"
    f"{SEASON_DESCRIPTION}"
  )

def build_tasks_text(tasks: list, hours_left_text: str, pass_tier: int) -> str:
  """Изменено: Применяет множитель x2 для Ультра и x3 для Мега."""
  lines = ["📋 <b>Текущие ежедневные задания:</b>\n"]

  for idx, task in enumerate(tasks, start=1):
    if task.get("claimed"):
      status = "🏆"
    elif task.get("is_completed"):
      status = "✅"
    else:
      status = "❌"

    progress = task.get("progress", 0)
    target = task.get("target", 1)
    reward = task.get("reward", 0)

    # Новая логика множителей
    if pass_tier == PASS_TIER_ULTRA:
      reward *= 2
    elif pass_tier == PASS_TIER_MEGA:
      reward *= 3

    lines.append(
      f"[{idx}] {task['text']} ({status})\n"
      f"Прогресс: {progress}/{target}\n"
      f"Награда: {reward} {CHERRY_EMOJI}\n"
    )

  lines.append(f"Обновление через {hours_left_text}")
  return "\n".join(lines)

def build_bonus_text(already_claimed: bool, pass_tier: int) -> str:
  """Изменено: Показывает правильный бонус для Ультра и Мега."""
  if already_claimed:
    return (
      "🎁 <b>Ежедневный бонус</b>\n\n"
      "Ты уже забрал бонус сегодня.\n"
      f"Возвращайся завтра за новой порцией {CHERRY_EMOJI}"
    )

  bonus_text = f"<b>{DAILY_BONUS_REWARD}</b> {CHERRY_EMOJI}"
  # Новая логика отображения бонуса
  if pass_tier == PASS_TIER_ULTRA:
    bonus_text += f" (+{ULTRA_PASS_DAILY_BONUS} {CHERRY_EMOJI} за Ультра)"
  elif pass_tier == PASS_TIER_MEGA:
    bonus_text += f" (+{MEGA_PASS_DAILY_BONUS} {CHERRY_EMOJI} за Мега)"

  return (
    "🎁 <b>Ежедневный бонус</b>\n\n"
    "Нажми кнопку ниже, чтобы забрать ежедневный бонус:\n"
    f"{bonus_text}"
  )

def build_info_text() -> str:
  """Полностью переписан для отображения информации о всех трех пропусках."""
  return (
    f"ℹ️ <b>Информация о пропуске</b>\n\n"
    f"<b>Общие сведения:</b>\n"
    f"— За каждый этап нужно {CHERRIES_PER_LEVEL} {CHERRY_EMOJI}\n"
    f"— Всего в сезоне {MAX_LEVEL - 10} основных этапов + 10 бонусных\n"
    f"— Ежедневный бонус: <b>{DAILY_BONUS_REWARD}</b> {CHERRY_EMOJI}\n"
    f"— Ежедневных заданий: <b>{DAILY_TASKS_COUNT}</b>\n\n"
    f"<tg-spoiler>"
    f"💠 <b>Преимущества Ультра ({ULTRA_PASS_COST} 🪙):</b>\n"
    f"— Награды за задания: <b>x2</b>\n"
    f"— Доп. бонус: <b>+{ULTRA_PASS_DAILY_BONUS}</b> {CHERRY_EMOJI}\n"
    f"— Доступ к Ультра-наградам за этапы\n\n"
    f"💎 <b>Преимущества Мега ({MEGA_PASS_COST} 🪙):</b>\n"
    f"— Награды за задания: <b>x3</b>\n"
    f"— Доп. бонус: <b>+{MEGA_PASS_DAILY_BONUS}</b> {CHERRY_EMOJI}\n"
    f"— Доп. ежедневное задание (всего {MEGA_PASS_TASKS_COUNT})\n"
    f"— Доступ к <b>+10 бонусным этапам</b> (41-50)\n"
    f"— Обмен {CHERRY_EMOJI} на 🪙 после 50-го уровня (1 к {CHERRY_TO_FRAG_RATE})\n"
    f"— Функция авто-сбора наград (скоро)\n"
    f"</tg-spoiler>"
  )