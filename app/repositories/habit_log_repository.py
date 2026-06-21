from typing import List, Optional, Dict
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import HabitLog, Habit


class HabitLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_habit_and_date(self, habit_id: int, log_date: date) -> Optional[HabitLog]:
        return self.db.query(HabitLog).filter(
            HabitLog.habit_id == habit_id,
            HabitLog.date == log_date,
        ).first()

    def get_by_habit_date_and_user(
        self, habit_id: int, log_date: date, user_id: int
    ) -> Optional[HabitLog]:
        return self.db.query(HabitLog).join(Habit).filter(
            HabitLog.habit_id == habit_id,
            HabitLog.date == log_date,
            Habit.user_id == user_id,
        ).first()

    def create(self, log: HabitLog) -> HabitLog:
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def delete(self, log: HabitLog) -> None:
        self.db.delete(log)
        self.db.commit()

    def update_note(self, log: HabitLog, note: str) -> HabitLog:
        log.note = note
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_for_date_range(
        self, habit_id: int, start_date: date, end_date: date, completed: int = 1
    ) -> List[HabitLog]:
        return self.db.query(HabitLog).filter(
            HabitLog.habit_id == habit_id,
            HabitLog.date >= start_date,
            HabitLog.date <= end_date,
            HabitLog.completed == completed,
        ).all()

    def get_for_month(
        self, habit_id: int, year: int, month: int
    ) -> List[HabitLog]:
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        return self.get_for_date_range(habit_id, start_date, end_date)

    def count_completed_for_habit(self, habit_id: int) -> int:
        return self.db.query(HabitLog).filter(
            HabitLog.habit_id == habit_id,
            HabitLog.completed == 1,
        ).count()

    def count_completed_for_habit_and_date(
        self, habit_id: int, log_date: date
    ) -> int:
        return self.db.query(HabitLog).filter(
            HabitLog.habit_id == habit_id,
            HabitLog.date == log_date,
            HabitLog.completed == 1,
        ).count()

    def get_logs_for_user_and_date(
        self, user_id: int, log_date: date
    ) -> Dict[int, bool]:
        habits = self.db.query(Habit).filter(Habit.user_id == user_id).all()
        habit_ids = [h.id for h in habits]
        logs = self.db.query(HabitLog).filter(
            HabitLog.habit_id.in_(habit_ids),
            HabitLog.date == log_date,
            HabitLog.completed == 1,
        ).all()
        result = {}
        for log in logs:
            result[log.habit_id] = True
        return result

    def get_logs_with_notes_for_user_and_date(
        self, user_id: int, log_date: date
    ) -> List[HabitLog]:
        return self.db.query(HabitLog).join(Habit).filter(
            Habit.user_id == user_id,
            HabitLog.date == log_date,
            HabitLog.completed == 1,
        ).all()

    def get_recent_notes(
        self, user_id: int, habit_id: Optional[int] = None, days: int = 30
    ) -> List[HabitLog]:
        today = date.today()
        start_date = today - timedelta(days=days - 1)
        query = self.db.query(HabitLog).join(Habit).filter(
            Habit.user_id == user_id,
            HabitLog.date >= start_date,
            HabitLog.completed == 1,
        )
        if habit_id:
            query = query.filter(HabitLog.habit_id == habit_id)
        return query.order_by(HabitLog.date.desc()).all()

    def count_for_user_and_date(self, user_id: int, log_date: date) -> int:
        return self.db.query(HabitLog).join(Habit).filter(
            Habit.user_id == user_id,
            HabitLog.date == log_date,
            HabitLog.completed == 1,
        ).count()

    def count_for_user_and_week(self, user_id: int) -> Dict[str, int]:
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        result = {}
        for i in range(7):
            day = start_of_week + timedelta(days=i)
            day_str = day.strftime("%Y-%m-%d")
            count = self.count_for_user_and_date(user_id, day)
            result[day_str] = count
        return result

    def count_for_user_and_month(
        self, user_id: int, year: int, month: int
    ) -> Dict[str, int]:
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
                count = self.count_for_user_and_date(user_id, d)
                result[day_str] = count
            except ValueError:
                pass
        return result

    def get_streak_data(
        self, habit_id: int, from_date: date
    ) -> List[date]:
        logs = self.db.query(HabitLog).filter(
            HabitLog.habit_id == habit_id,
            HabitLog.date <= from_date,
            HabitLog.completed == 1,
        ).order_by(HabitLog.date.desc()).all()
        return [log.date for log in logs]
