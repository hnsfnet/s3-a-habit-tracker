from typing import List, Optional
from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session

from app.models import Habit, HabitLog, User
from app.schemas import HabitCreate, HabitUpdate, HabitWithStats


def get_habits_by_user(db: Session, user_id: int) -> List[Habit]:
    return db.query(Habit).filter(Habit.user_id == user_id).order_by(Habit.created_at.desc()).all()


def get_habit_by_id(db: Session, habit_id: int, user_id: int) -> Optional[Habit]:
    return db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()


def create_habit(db: Session, habit_create: HabitCreate, user_id: int) -> Habit:
    db_habit = Habit(
        name=habit_create.name,
        description=habit_create.description,
        category=habit_create.category,
        frequency_type=habit_create.frequency_type,
        frequency_count=habit_create.frequency_count,
        user_id=user_id,
    )
    db.add(db_habit)
    db.commit()
    db.refresh(db_habit)
    return db_habit


def update_habit(db: Session, habit_id: int, habit_update: HabitUpdate, user_id: int) -> Optional[Habit]:
    habit = get_habit_by_id(db, habit_id, user_id)
    if not habit:
        return None
    update_data = habit_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(habit, key, value)
    db.commit()
    db.refresh(habit)
    return habit


def delete_habit(db: Session, habit_id: int, user_id: int) -> bool:
    habit = get_habit_by_id(db, habit_id, user_id)
    if not habit:
        return False
    db.delete(habit)
    db.commit()
    return True


def calculate_current_streak(db: Session, habit_id: int) -> int:
    today = date.today()
    streak = 0
    current_date = today

    while True:
        log = db.query(HabitLog).filter(
            HabitLog.habit_id == habit_id,
            HabitLog.date == current_date,
            HabitLog.completed == 1,
        ).first()
        if log:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            if current_date == today:
                yesterday = today - timedelta(days=1)
                log_yesterday = db.query(HabitLog).filter(
                    HabitLog.habit_id == habit_id,
                    HabitLog.date == yesterday,
                    HabitLog.completed == 1,
                ).first()
                if not log_yesterday:
                    return 0
                current_date = yesterday
            else:
                break

    return streak


def calculate_total_completed(db: Session, habit_id: int) -> int:
    return db.query(HabitLog).filter(
        HabitLog.habit_id == habit_id,
        HabitLog.completed == 1,
    ).count()


def calculate_completion_rate(db: Session, habit_id: int) -> float:
    habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if not habit:
        return 0.0

    created_date = habit.created_at.date()
    today = date.today()
    days_since_created = (today - created_date).days + 1

    if days_since_created <= 0:
        return 0.0

    total_completed = calculate_total_completed(db, habit_id)

    if habit.frequency_type == "daily":
        expected = days_since_created
    elif habit.frequency_type == "weekly":
        expected = (days_since_created // 7 + 1) * habit.frequency_count
    elif habit.frequency_type == "monthly":
        months = (today.year - created_date.year) * 12 + (today.month - created_date.month) + 1
        expected = months * habit.frequency_count
    else:
        expected = days_since_created

    if expected <= 0:
        return 0.0

    rate = min((total_completed / expected) * 100, 100.0)
    return round(rate, 1)


def get_habits_with_stats(db: Session, user_id: int) -> List[HabitWithStats]:
    habits = get_habits_by_user(db, user_id)
    result = []
    for habit in habits:
        streak = calculate_current_streak(db, habit.id)
        total = calculate_total_completed(db, habit.id)
        rate = calculate_completion_rate(db, habit.id)
        habit_with_stats = HabitWithStats(
            id=habit.id,
            name=habit.name,
            description=habit.description,
            category=habit.category,
            frequency_type=habit.frequency_type,
            frequency_count=habit.frequency_count,
            user_id=habit.user_id,
            created_at=habit.created_at,
            current_streak=streak,
            total_completed=total,
            completion_rate=rate,
        )
        result.append(habit_with_stats)
    return result
