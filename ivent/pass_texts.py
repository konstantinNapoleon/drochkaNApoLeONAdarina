from ivent.pass_data import SEASON_TITLE, SEASON_DESCRIPTION


def build_main_menu_text(user_level: int, is_ultra: bool, days_left: int) -> str:
    pass_type = "Ультра" if is_ultra else "Обычный"

    return (
        f"{SEASON_TITLE}\n\n"
        f"— Твой уровень: {user_level}\n"
        f"— Пропуск: {pass_type}\n"
        f"— До окончания сезона: {days_left} д.\n\n"
        f"{SEASON_DESCRIPTION}"
    )


def build_tasks_text(tasks: list, hours_left_text: str) -> str:
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

        lines.append(
            f"[{idx}] {task['text']} ({status})\n"
            f"Прогресс: {progress}/{target}\n"
            f"Награда: {reward} 🍑\n"
        )

    lines.append(f"Обновление через {hours_left_text}")
    return "\n".join(lines)



def build_bonus_text(already_claimed: bool) -> str:
    if already_claimed:
        return (
            "🎁 <b>Ежедневный бонус</b>\n\n"
            "Ты уже забрал бонус сегодня.\n"
            "Возвращайся завтра за новой порцией 🍑"
        )

    return (
        "🎁 <b>Ежедневный бонус</b>\n\n"
        "Нажми кнопку ниже, чтобы забрать ежедневный бонус:\n"
        "50 🍑"
    )


def build_info_text() -> str:
    return (
        "ℹ️ <b>Информация о пропуске</b>\n\n"
        "— За каждый уровень нужно 150 🍑\n"
        "— Всего в сезоне 10 уровней\n"
        "— Каждый день выдается 3 случайных задания\n"
        "— Также доступен ежедневный бонус 50 🍑\n"
        "— Награды можно забирать по мере достижения уровней\n"
        "— Если у тебя есть Ультра пропуск, позже можно будет открыть доп. возможности"
    )
