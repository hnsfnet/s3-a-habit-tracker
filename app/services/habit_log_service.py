from typing import List, Optional, Dict
from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session

from app.models import HabitLog, Habit, User


def get_log_by_habit_and_date(db: Session, habit_id: int, log_date: date) -> Optional[HabitLog]:
    return db.query(HabitLog).filter(
        HabitLog.habit_id == habit_id,
        HabitLog.date == log_date,
    ).first()


def toggle_habit_log(db: Session, habit_id: int, user_id: int, log_date: date) -> Optional[HabitLog]:
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    if not habit:
        return None

    existing_log = get_log_by_habit_and_date(db, habit_id, log_date)
    if existing_log:
        db.delete(existing_log)
        db.commit()
        return None
    else:
        new_log = HabitLog(
            habit_id=habit_id,
            date=log_date,
            completed=1,
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return new_log


def get_logs_for_date_range(db: Session, habit_id: int, start_date: date, end_date: date) -> List[HabitLog]:
    return db.query(HabitLog).filter(
        HabitLog.habit_id == habit_id,
        HabitLog.date >= start_date,
        HabitLog.date <= end_date,
        HabitLog.completed == 1,
    ).all()


def get_user_logs_for_date(db: Session, user_id: int, log_date: date) -> Dict[int, bool]:
    habits = db.query(Habit).filter(Habit.user_id == user_id).all()
    habit_ids = [h.id for h in habits]

    logs = db.query(HabitLog).filter(
        HabitLog.habit_id.in_(habit_ids),
        HabitLog.date == log_date,
        HabitLog.completed == 1,
    ).all()

    result = {}
    for log in logs:
        result[log.habit_id] = True
    return result


def get_weekly_completion(db: Session, user_id: int) -> Dict[str, int]:
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    result = {}

    for i in range(7):
        day = start_of_week + timedelta(days=i)
        day_name = day.strftime("%A")
        day_str = day.strftime("%Y-%m-%d")
        count = db.query(HabitLog).join(Habit).filter(
            Habit.user_id == user_id,
            HabitLog.date == day,
            HabitLog.completed == 1,
        ).count()
        result[day_str] = count

    return result


def get_monthly_completion(db: Session, user_id: int, year: int = None, month: int = None) -> Dict[str, int]:
    if year is None:
        year = date.today().year
    if month is None:
        month = date.today().month

    result = {}
    days_in_month = 31
    if month == 2:
        days_in_month = 29 if year % 4 == 0 else 28
    elif month in [4, 6, 9, 11]:
        days_in_month = 30

    for day in range(1, days_in_month + 1):
        try:
            d = date(year, month, day)
            day_str = d.strftime("%Y-%m-%d")
            count = db.query(HabitLog).join(Habit).filter(
                Habit.user_id == user_id,
                HabitLog.date == d,
                HabitLog.completed == 1,
            ).count()
            result[day_str] = count
        except ValueError:
            pass

    return result


def get_habit_logs_for_month(db: Session, habit_id: int, year: int, month: int) -> List[HabitLog]:
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)

    return db.query(HabitLog).filter(
        HabitLog.habit_id == habit_id,
        HabitLog.date >= start_date,
        HabitLog.date <= end_date,
        HabitLog.completed == 1,
    ).all()
