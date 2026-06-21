from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session

from app.models import Habit, HabitLog, Challenge


class HabitRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user(self, user_id: int) -> List[Habit]:
        return self.db.query(Habit).filter(
            Habit.user_id == user_id
        ).order_by(Habit.created_at.desc()).all()

    def get_by_id(self, habit_id: int, user_id: int) -> Optional[Habit]:
        return self.db.query(Habit).filter(
            Habit.id == habit_id,
            Habit.user_id == user_id
        ).first()

    def get_by_id_any_user(self, habit_id: int) -> Optional[Habit]:
        return self.db.query(Habit).filter(Habit.id == habit_id).first()

    def create(self, habit: Habit) -> Habit:
        self.db.add(habit)
        self.db.commit()
        self.db.refresh(habit)
        return habit

    def update(self, habit: Habit) -> Habit:
        self.db.commit()
        self.db.refresh(habit)
        return habit

    def delete(self, habit_id: int, user_id: int) -> bool:
        habit = self.get_by_id(habit_id, user_id)
        if not habit:
            return False
        self.db.delete(habit)
        self.db.commit()
        return True

    def delete_with_related(self, habit_id: int, user_id: int) -> bool:
        habit = self.get_by_id(habit_id, user_id)
        if not habit:
            return False
        self.db.query(HabitLog).filter(HabitLog.habit_id == habit_id).delete()
        self.db.query(Challenge).filter(Challenge.habit_id == habit_id).delete()
        self.db.delete(habit)
        self.db.commit()
        return True

    def count_by_user(self, user_id: int) -> int:
        return self.db.query(Habit).filter(Habit.user_id == user_id).count()
