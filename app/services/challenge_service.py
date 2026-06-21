from typing import List, Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.models import Challenge, Habit, HabitLog
from app.schemas import ChallengeCreate, ChallengeUpdate, ChallengeWithStats
from app.repositories import ChallengeRepository, HabitRepository


def create_challenge(db: Session, challenge_create: ChallengeCreate, user_id: int) -> Optional[Challenge]:
    habit_repo = HabitRepository(db)
    habit = habit_repo.get_by_id(challenge_create.habit_id, user_id)
    if not habit:
        return None

    end_date = challenge_create.start_date + timedelta(days=challenge_create.target_days - 1)

    challenge = Challenge(
        habit_id=challenge_create.habit_id,
        user_id=user_id,
        name=challenge_create.name,
        target_days=challenge_create.target_days,
        start_date=challenge_create.start_date,
        end_date=end_date,
        is_completed=False,
    )
    challenge_repo = ChallengeRepository(db)
    return challenge_repo.create(challenge)


def get_challenges_by_user(db: Session, user_id: int) -> List[Challenge]:
    repo = ChallengeRepository(db)
    return repo.get_by_user(user_id)


def get_challenge_by_id(db: Session, challenge_id: int, user_id: int) -> Optional[Challenge]:
    repo = ChallengeRepository(db)
    return repo.get_by_id(challenge_id, user_id)


def update_challenge(db: Session, challenge_id: int, challenge_update: ChallengeUpdate, user_id: int) -> Optional[Challenge]:
    repo = ChallengeRepository(db)
    challenge = repo.get_by_id(challenge_id, user_id)
    if not challenge:
        return None

    if challenge_update.name is not None:
        challenge.name = challenge_update.name

    return repo.update(challenge)


def delete_challenge(db: Session, challenge_id: int, user_id: int) -> bool:
    repo = ChallengeRepository(db)
    return repo.delete(challenge_id, user_id)


def calculate_challenge_progress(db: Session, challenge: Challenge) -> ChallengeWithStats:
    today = date.today()
    habit_repo = HabitRepository(db)
    challenge_repo = ChallengeRepository(db)
    habit = habit_repo.get_by_id_any_user(challenge.habit_id)

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

    logs = challenge_repo.get_logs_for_challenge(challenge)

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
            challenge_repo.update(challenge)

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
    repo = ChallengeRepository(db)
    return repo.get_active_for_habit(habit_id, user_id)
