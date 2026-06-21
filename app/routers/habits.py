from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import HabitCreate, HabitUpdate, HabitResponse, HabitWithStats
from app.services import (
    get_current_user,
    get_habit_by_id,
    create_habit,
    update_habit,
    delete_habit,
    get_habits_with_stats,
)

router = APIRouter(prefix="/api/habits", tags=["habits"])


@router.get("/", response_model=List[HabitWithStats])
def list_habits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_habits_with_stats(db, current_user.id)


@router.post("/", response_model=HabitResponse)
def create_new_habit(
    habit_create: HabitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = create_habit(db, habit_create, current_user.id)
    return habit


@router.get("/{habit_id}", response_model=HabitWithStats)
def get_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = get_habit_by_id(db, habit_id, current_user.id)
    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found",
        )
    from app.services import (
        calculate_current_streak,
        calculate_total_completed,
        calculate_completion_rate,
    )
    streak = calculate_current_streak(db, habit.id)
    total = calculate_total_completed(db, habit.id)
    rate = calculate_completion_rate(db, habit.id)
    return HabitWithStats(
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


@router.put("/{habit_id}", response_model=HabitResponse)
def update_existing_habit(
    habit_id: int,
    habit_update: HabitUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = update_habit(db, habit_id, habit_update, current_user.id)
    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found",
        )
    return habit


@router.delete("/{habit_id}")
def delete_existing_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    success = delete_habit(db, habit_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit not found",
        )
    return {"message": "Habit deleted successfully"}
