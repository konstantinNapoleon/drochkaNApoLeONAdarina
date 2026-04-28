from .pass_db import get_or_create_today_tasks, update_task_progress, add_peaches


async def progress_task(user_id: int, task_id: str, amount: int = 1):
    """
    Добавляет прогресс к ежедневному заданию пользователя.
    Если нужного задания на сегодня нет — просто ничего не делает.
    """
    tasks = await get_or_create_today_tasks(user_id)

    for task in tasks:
        if task["task_id"] != task_id:
            continue

        if task.get("claimed"):
            return False

        current = int(task.get("progress", 0))
        target = int(task.get("target", 1))

        if current >= target:
            return False

        new_progress = current + amount
        if new_progress > target:
            new_progress = target

        is_completed = new_progress >= target

        await update_task_progress(
            task_row_id=task["id"],
            progress=new_progress,
            is_completed=is_completed
        )
        return True

    return False


async def claim_task_reward(user_id: int, task_row_id: int):
    """
    Забирает награду за выполненное ежедневное задание.
    """
    from .pass_db import get_today_tasks, get_db_connection

    tasks = await get_today_tasks(user_id)
    target_task = None

    for task in tasks:
        if int(task["id"]) == int(task_row_id):
            target_task = task
            break

    if not target_task:
        return False, "Задание не найдено"

    if target_task.get("claimed"):
        return False, "Награда уже получена"

    if not target_task.get("is_completed"):
        return False, "Задание еще не выполнено"

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE ivent_pass_daily_tasks
            SET claimed = TRUE
            WHERE id = %s
        """, (task_row_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    reward = int(target_task.get("reward", 0))
    new_peaches = await add_peaches(user_id, reward)

    return True, new_peaches
