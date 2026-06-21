from typing import Dict, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.services import (
    get_current_user,
    toggle_habit_log,
    get_weekly_completion,
    get_monthly_completion,
    get_user_logs_for_date,
)

router = APIRouter(prefix="/api/habit-logs", tags=["habit-logs"])


@router.post("/toggle/{habit_id}")
def toggle_log(
    habit_id: int,
    log_date: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = toggle_habit_log(db, habit_id, current_user.id, log_date)
    if result is None and get_user_logs_for_date(db, current_user.id, log_date).get(habit_id) is None:
        return {"completed": False, "message": "Habit unchecked"}
    return {"completed": True, "message": "Habit checked"}


@router.get("/weekly")
def weekly_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_weekly_completion(db, current_user.id)


@router.get("/monthly")
def monthly_stats(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_monthly_completion(db, current_user.id, year, month)


@router.get("/date/{log_date}")
def logs_for_date(
    log_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_user_logs_for_date(db, current_user.id, log_date)
