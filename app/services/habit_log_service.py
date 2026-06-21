from typing import List, Optional, Dict
from datetime import date
from sqlalchemy.orm import Session

from app.models import HabitLog, Habit
from app.schemas import HabitLogWithNote
from app.repositories import HabitLogRepository, HabitRepository


def toggle_habit_log(
    db: Session,
    habit_id: int,
    user_id: int,
    log_date: date,
    note: str = "",
) -> Optional[HabitLog]:
    habit_repo = HabitRepository(db)
    habit = habit_repo.get_by_id(habit_id, user_id)
    if not habit:
        return None

    log_repo = HabitLogRepository(db)
    existing_log = log_repo.get_by_habit_and_date(habit_id, log_date)
    if existing_log:
        log_repo.delete(existing_log)
        return None
    else:
        new_log = HabitLog(
            habit_id=habit_id,
            date=log_date,
            completed=1,
            note=note,
        )
        return log_repo.create(new_log)


def update_log_note(
    db: Session,
    habit_id: int,
    user_id: int,
    log_date: date,
    note: str,
) -> Optional[HabitLog]:
    log_repo = HabitLogRepository(db)
    log = log_repo.get_by_habit_date_and_user(habit_id, log_date, user_id)
    if not log:
        return None
    return log_repo.update_note(log, note)


def get_user_logs_for_date(db: Session, user_id: int, log_date: date) -> Dict[int, bool]:
    log_repo = HabitLogRepository(db)
    return log_repo.get_logs_for_user_and_date(user_id, log_date)


def get_user_logs_with_notes_for_date(
    db: Session,
    user_id: int,
    log_date: date,
) -> Dict[int, Dict]:
    log_repo = HabitLogRepository(db)
    logs = log_repo.get_logs_with_notes_for_user_and_date(user_id, log_date)
    result = {}
    for log in logs:
        result[log.habit_id] = {
            "completed": True,
            "note": log.note or "",
        }
    return result


def get_recent_notes(
    db: Session,
    user_id: int,
    habit_id: Optional[int] = None,
    days: int = 30,
) -> List[HabitLogWithNote]:
    log_repo = HabitLogRepository(db)
    logs = log_repo.get_recent_notes(user_id, habit_id, days)
    result = []
    for log in logs:
        result.append(HabitLogWithNote(
            id=log.id,
            habit_id=log.habit_id,
            date=log.date,
            completed=log.completed,
            note=log.note or "",
            created_at=log.created_at,
            habit_name=log.habit.name,
        ))
    return result


def get_weekly_completion(db: Session, user_id: int) -> Dict[str, int]:
    log_repo = HabitLogRepository(db)
    return log_repo.count_for_user_and_week(user_id)


def get_monthly_completion(
    db: Session, user_id: int, year: int = None, month: int = None
) -> Dict[str, int]:
    if year is None:
        year = date.today().year
    if month is None:
        month = date.today().month
    log_repo = HabitLogRepository(db)
    return log_repo.count_for_user_and_month(user_id, year, month)
