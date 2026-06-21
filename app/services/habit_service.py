from typing import List, Optional
from sqlalchemy.orm import Session

from app.models import Habit
from app.schemas import HabitCreate, HabitUpdate
from app.repositories import HabitRepository


def get_habits_by_user(db: Session, user_id: int) -> List[Habit]:
    repo = HabitRepository(db)
    return repo.get_by_user(user_id)


def get_habit_by_id(db: Session, habit_id: int, user_id: int) -> Optional[Habit]:
    repo = HabitRepository(db)
    return repo.get_by_id(habit_id, user_id)


def create_habit(db: Session, habit_create: HabitCreate, user_id: int) -> Habit:
    habit = Habit(
        name=habit_create.name,
        description=habit_create.description,
        category=habit_create.category,
        frequency_type=habit_create.frequency_type,
        frequency_count=habit_create.frequency_count,
        user_id=user_id,
    )
    repo = HabitRepository(db)
    return repo.create(habit)


def update_habit(db: Session, habit_id: int, habit_update: HabitUpdate, user_id: int) -> Optional[Habit]:
    repo = HabitRepository(db)
    habit = repo.get_by_id(habit_id, user_id)
    if not habit:
        return None
    update_data = habit_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(habit, key, value)
    return repo.update(habit)


def delete_habit(db: Session, habit_id: int, user_id: int) -> bool:
    repo = HabitRepository(db)
    return repo.delete_with_related(habit_id, user_id)
