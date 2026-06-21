from typing import List, Optional, Dict
from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session

from app.models import Challenge, Habit, HabitLog, User
from app.schemas import ChallengeCreate, ChallengeUpdate, ChallengeWithStats


def create_challenge(db: Session, challenge_create: ChallengeCreate, user_id: int) -> Challenge:
    habit = db.query(Habit).filter(
        Habit.id == challenge_create.habit_id,
        Habit.user_id == user_id,
    ).first()
    if not habit:
        return None
    
    end_date = challenge_create.start_date + timedelta(days=challenge_create.target_days - 1)
    
    db_challenge = Challenge(
        habit_id=challenge_create.habit_id,
        user_id=user_id,
        name=challenge_create.name,
        target_days=challenge_create.target_days,
        start_date=challenge_create.start_date,
        end_date=end_date,
        is_completed=False,
    )
    db.add(db_challenge)
    db.commit()
    db.refresh(db_challenge)
    return db_challenge


def get_challenges_by_user(db: Session, user_id: int) -> List[Challenge]:
    return db.query(Challenge).filter(
        Challenge.user_id == user_id,
    ).order_by(Challenge.created_at.desc()).all()


def get_challenge_by_id(db: Session, challenge_id: int, user_id: int) -> Optional[Challenge]:
    return db.query(Challenge).filter(
        Challenge.id == challenge_id,
        Challenge.user_id == user_id,
    ).first()


def update_challenge(db: Session, challenge_id: int, challenge_update: ChallengeUpdate, user_id: int) -> Optional[Challenge]:
    challenge = get_challenge_by_id(db, challenge_id, user_id)
    if not challenge:
        return None
    
    if challenge_update.name is not None:
        challenge.name = challenge_update.name
    
    db.commit()
    db.refresh(challenge)
    return challenge


def delete_challenge(db: Session, challenge_id: int, user_id: int) -> bool:
    challenge = get_challenge_by_id(db, challenge_id, user_id)
    if not challenge:
        return False
    db.delete(challenge)
    db.commit()
    return True


def calculate_challenge_progress(db: Session, challenge: Challenge) -> ChallengeWithStats:
    today = date.today()
    habit = db.query(Habit).filter(Habit.id == challenge.habit_id).first()
    
    if today < challenge.start_date:
        return ChallengeWithStats(
            id=challenge.id,
            habit_id=challenge.habit_id,
            user_id=challenge.user_id,
            name=challenge.name,
            target_days=challenge.target_days,
            start_date=challenge.start_date,
            end_date=challenge.end_date,
            is_completed=challenge.is_completed,
            completed_date=challenge.completed_date,
            created_at=challenge.created_at,
            current_progress=0,
            current_streak=0,
            remaining_days=(challenge.end_date - today).days + 1,
            progress_percent=0.0,
            daily_status={},
            habit_name=habit.name if habit else None,
        )
    
    end_date = min(challenge.end_date, today)
    
    logs = db.query(HabitLog).filter(
        HabitLog.habit_id == challenge.habit_id,
        HabitLog.date >= challenge.start_date,
        HabitLog.date <= end_date,
        HabitLog.completed == 1,
    ).all()
    
    completed_dates = set()
    for log in logs:
        if challenge.start_date <= log.date <= end_date:
            completed_dates.add(log.date)
    
    current_progress = len(completed_dates)
    
    current_streak = 0
    check_date = end_date
    
    while check_date >= challenge.start_date:
        if check_date in completed_dates:
            current_streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    
    if today > challenge.end_date:
        remaining_days = 0
    else:
        remaining_days = (challenge.end_date - today).days + 1
    
    progress_percent = round((current_progress / challenge.target_days) * 100, 1)
    
    daily_status = {}
    current_date = challenge.start_date
    while current_date <= end_date:
        daily_status[current_date.strftime("%Y-%m-%d")] = current_date in completed_dates
        current_date += timedelta(days=1)
    
    was_completed = challenge.is_completed
    actual_completed_date = None
    
    if current_progress >= challenge.target_days:
        sorted_dates = sorted(completed_dates)
        if len(sorted_dates) >= challenge.target_days:
            actual_completed_date = sorted_dates[challenge.target_days - 1]
        
        if not was_completed:
            challenge.is_completed = True
            challenge.completed_date = actual_completed_date
            db.commit()
            db.refresh(challenge)
    
    habit = db.query(Habit).filter(Habit.id == challenge.habit_id).first()
    
    return ChallengeWithStats(
        id=challenge.id,
        habit_id=challenge.habit_id,
        user_id=challenge.user_id,
        name=challenge.name,
        target_days=challenge.target_days,
        start_date=challenge.start_date,
        end_date=challenge.end_date,
        is_completed=challenge.is_completed,
        completed_date=challenge.completed_date,
        created_at=challenge.created_at,
        current_progress=current_progress,
        current_streak=current_streak,
        remaining_days=remaining_days,
        progress_percent=progress_percent,
        daily_status=daily_status,
        habit_name=habit.name if habit else None,
    )


def get_challenges_with_stats(db: Session, user_id: int) -> List[ChallengeWithStats]:
    challenges = get_challenges_by_user(db, user_id)
    return [calculate_challenge_progress(db, c) for c in challenges]


def get_active_challenge_for_habit(db: Session, habit_id: int, user_id: int) -> Optional[Challenge]:
    today = date.today()
    return db.query(Challenge).filter(
        Challenge.habit_id == habit_id,
        Challenge.user_id == user_id,
        Challenge.is_completed == False,
        Challenge.start_date <= today,
        Challenge.end_date >= today,
    ).first()
