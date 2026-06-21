from typing import List, Dict, Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.models import Habit, HabitLog
from app.schemas import (
    Stats30DayTrend,
    StatsCategoryBreakdown,
    StatsMonthlyRate,
    HabitWithStats,
)
from app.repositories import HabitRepository, HabitLogRepository
from app.services.habit_log_service import (
    get_user_logs_for_date,
    get_weekly_completion,
)


def calculate_current_streak(db: Session, habit_id: int) -> int:
    today = date.today()
    streak = 0
    check_date = today

    log_repo = HabitLogRepository(db)
    log_today = log_repo.get_by_habit_and_date(habit_id, today)

    if not log_today or log_today.completed != 1:
        check_date = today - timedelta(days=1)

    while True:
        log = log_repo.get_by_habit_and_date(habit_id, check_date)
        if log and log.completed == 1:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    return streak


def calculate_total_completed(db: Session, habit_id: int) -> int:
    log_repo = HabitLogRepository(db)
    return log_repo.count_completed_for_habit(habit_id)


def calculate_completion_rate(db: Session, habit_id: int) -> float:
    habit_repo = HabitRepository(db)
    habit = habit_repo.get_by_id_any_user(habit_id)
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


def get_habit_with_stats(db: Session, habit: Habit) -> HabitWithStats:
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


def get_habits_with_stats(db: Session, user_id: int) -> List[HabitWithStats]:
    habit_repo = HabitRepository(db)
    habits = habit_repo.get_by_user(user_id)
    return [get_habit_with_stats(db, habit) for habit in habits]


def get_30day_trend(db: Session, user_id: int) -> List[Stats30DayTrend]:
    today = date.today()
    result = []
    log_repo = HabitLogRepository(db)

    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        count = log_repo.count_for_user_and_date(user_id, d)
        result.append(Stats30DayTrend(
            date=d.strftime("%Y-%m-%d"),
            count=count,
        ))

    return result


def get_category_breakdown(db: Session, user_id: int) -> List[StatsCategoryBreakdown]:
    habit_repo = HabitRepository(db)
    log_repo = HabitLogRepository(db)
    habits = habit_repo.get_by_user(user_id)
    if not habits:
        return []

    category_counts = {}
    for habit in habits:
        count = log_repo.count_completed_for_habit(habit.id)
        if habit.category not in category_counts:
            category_counts[habit.category] = 0
        category_counts[habit.category] += count

    total = sum(category_counts.values())

    result = []
    for category, count in category_counts.items():
        percentage = round((count / total) * 100, 1) if total > 0 else 0
        result.append(StatsCategoryBreakdown(
            category=category,
            count=count,
            percentage=percentage,
        ))

    return result


def get_monthly_completion_rates(
    db: Session,
    user_id: int,
    habit_id: Optional[int] = None,
) -> List[StatsMonthlyRate]:
    today = date.today()
    result = []
    habit_repo = HabitRepository(db)
    log_repo = HabitLogRepository(db)

    for i in range(5, -1, -1):
        month_date = today - timedelta(days=i * 30)
        year = month_date.year
        month = month_date.month

        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        if end_date > today:
            end_date = today

        habits_query = habit_repo.get_by_user(user_id)
        habits = [h for h in habits_query if habit_id is None or h.id == habit_id]

        if not habits:
            result.append(StatsMonthlyRate(
                month=f"{year}年{month}月",
                rate=0.0,
            ))
            continue

        total_expected = 0
        total_completed = 0

        for habit in habits:
            days_in_period = (end_date - max(start_date, habit.created_at.date())).days + 1
            if days_in_period <= 0:
                continue

            logs = log_repo.get_for_date_range(
                habit.id, max(start_date, habit.created_at.date()), end_date)
            completed = len(logs)

            if habit.frequency_type == "daily":
                expected = days_in_period
            elif habit.frequency_type == "weekly":
                expected = (days_in_period // 7 + 1) * habit.frequency_count
            elif habit.frequency_type == "monthly":
                expected = habit.frequency_count
            else:
                expected = days_in_period

            total_expected += expected
            total_completed += completed

        rate = round((total_completed / total_expected) * 100, 1) if total_expected > 0 else 0
        rate = min(rate, 100.0)

        result.append(StatsMonthlyRate(
            month=f"{year}年{month}月",
            rate=rate,
        ))

    return result


def get_habit_monthly_rates(
    db: Session,
    habit_id: int,
    user_id: int,
) -> List[StatsMonthlyRate]:
    return get_monthly_completion_rates(db, user_id, habit_id)


def get_overall_stats(db: Session, user_id: int) -> Dict:
    habit_repo = HabitRepository(db)
    log_repo = HabitLogRepository(db)
    habits = habit_repo.get_by_user(user_id)
    habit_ids = [h.id for h in habits]

    total_logs = 0
    for habit_id in habit_ids:
        total_logs += log_repo.count_completed_for_habit(habit_id)

    today = date.today()
    today_completed = log_repo.count_for_user_and_date(user_id, today)

    week_start = today - timedelta(days=today.weekday())
    week_completed = 0
    for i in range(7):
        d = week_start + timedelta(days=i)
        week_completed += log_repo.count_for_user_and_date(user_id, d)

    max_streak = 0
    for habit in habits:
        streak = calculate_current_streak(db, habit.id)
        if streak > max_streak:
            max_streak = streak

    return {
        "total_habits": len(habits),
        "total_completions": total_logs,
        "today_completed": today_completed,
        "week_completed": week_completed,
        "max_streak": max_streak,
    }


def get_dashboard_stats(db: Session, user_id: int) -> Dict:
    habits = get_habits_with_stats(db, user_id)
    total_habits = len(habits)

    today = date.today()
    today_logs = get_user_logs_for_date(db, user_id, today)
    today_completed = len(today_logs)

    weekly_data = get_weekly_completion(db, user_id)
    week_total = sum(weekly_data.values())

    max_streak = 0
    for habit in habits:
        if habit.current_streak > max_streak:
            max_streak = habit.current_streak

    return {
        "habits": habits,
        "total_habits": total_habits,
        "today_completed": today_completed,
        "week_total": week_total,
        "max_streak": max_streak,
    }
