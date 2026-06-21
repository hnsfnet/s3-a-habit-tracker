from typing import Dict, Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import HabitLogUpdateNote, HabitLogWithNote
from app.services import (
    get_current_user,
    toggle_habit_log,
    update_log_note,
    get_user_logs_for_date,
    get_user_logs_with_notes_for_date,
    get_recent_notes,
    get_weekly_completion,
    get_monthly_completion,
)

router = APIRouter(prefix="/api/habit-logs", tags=["habit-logs"])


@router.post("/toggle/{habit_id}")
def toggle_log(
    habit_id: int,
    log_date: date = Query(default_factory=date.today),
    note: str = Query(default=""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = toggle_habit_log(db, habit_id, current_user.id, log_date, note)
    if result is None:
        existing_logs = get_user_logs_for_date(db, current_user.id, log_date)
        if existing_logs.get(habit_id) is None:
            return {"completed": False, "message": "Habit unchecked"}
    return {"completed": True, "message": "Habit checked"}


@router.put("/note/{habit_id}/{log_date}")
def update_note(
    habit_id: int,
    log_date: date,
    note_update: HabitLogUpdateNote,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = update_log_note(db, habit_id, current_user.id, log_date, note_update.note)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log not found",
        )
    return {"message": "Note updated successfully", "note": log.note}


@router.get("/date/{log_date}/with-notes")
def logs_for_date_with_notes(
    log_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_user_logs_with_notes_for_date(db, current_user.id, log_date)


@router.get("/recent-notes", response_model=List[HabitLogWithNote])
def recent_notes(
    habit_id: Optional[int] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_recent_notes(db, current_user.id, habit_id, days)


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
