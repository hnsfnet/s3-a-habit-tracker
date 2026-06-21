from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session

from app.models import Challenge, Habit, HabitLog


class ChallengeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user(self, user_id: int) -> List[Challenge]:
        return self.db.query(Challenge).filter(
            Challenge.user_id == user_id,
        ).order_by(Challenge.created_at.desc()).all()

    def get_by_id(self, challenge_id: int, user_id: int) -> Optional[Challenge]:
        return self.db.query(Challenge).filter(
            Challenge.id == challenge_id,
            Challenge.user_id == user_id,
        ).first()

    def create(self, challenge: Challenge) -> Challenge:
        self.db.add(challenge)
        self.db.commit()
        self.db.refresh(challenge)
        return challenge

    def update(self, challenge: Challenge) -> Challenge:
        self.db.commit()
        self.db.refresh(challenge)
        return challenge

    def delete(self, challenge_id: int, user_id: int) -> bool:
        challenge = self.get_by_id(challenge_id, user_id)
        if not challenge:
            return False
        self.db.delete(challenge)
        self.db.commit()
        return True

    def get_active_for_habit(
        self, habit_id: int, user_id: int
    ) -> Optional[Challenge]:
        today = date.today()
        return self.db.query(Challenge).filter(
            Challenge.habit_id == habit_id,
            Challenge.user_id == user_id,
            Challenge.is_completed == False,
            Challenge.start_date <= today,
            Challenge.end_date >= today,
        ).first()

    def get_logs_for_challenge(
        self, challenge: Challenge
    ) -> List[HabitLog]:
        today = date.today()
        end_date = min(challenge.end_date, today)
        return self.db.query(HabitLog).filter(
            HabitLog.habit_id == challenge.habit_id,
            HabitLog.date >= challenge.start_date,
            HabitLog.date <= end_date,
            HabitLog.completed == 1,
        ).all()

    def count_by_user(self, user_id: int) -> int:
        return self.db.query(Challenge).filter(
            Challenge.user_id == user_id
        ).count()
