from typing import List, Dict, Optional
from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Habit, HabitLog, User
from app.schemas import (
    Stats30DayTrend,
    StatsCategoryBreakdown,
    StatsMonthlyRate,
)


def get_30day_trend(db: Session, user_id: int) -> List[Stats30DayTrend]:
    today = date.today()
    result = []
    
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        count = db.query(HabitLog).join(Habit).filter(
            Habit.user_id == user_id,
            HabitLog.date == d,
            HabitLog.completed == 1,
        ).count()
        result.append(Stats30DayTrend(
            date=d.strftime("%Y-%m-%d"),
            count=count,
        ))
    
    return result


def get_category_breakdown(db: Session, user_id: int) -> List[StatsCategoryBreakdown]:
    habits = db.query(Habit).filter(Habit.user_id == user_id).all()
    if not habits:
        return []
    
    category_counts = {}
    for habit in habits:
        count = db.query(HabitLog).filter(
            HabitLog.habit_id == habit.id,
            HabitLog.completed == 1,
        ).count()
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
        
        habits_query = db.query(Habit).filter(Habit.user_id == user_id)
        if habit_id:
            habits_query = habits_query.filter(Habit.id == habit_id)
        habits = habits_query.all()
        
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
            
            completed = db.query(HabitLog).filter(
                HabitLog.habit_id == habit.id,
                HabitLog.date >= max(start_date, habit.created_at.date()),
                HabitLog.date <= end_date,
                HabitLog.completed == 1,
            ).count()
            
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
    habits = db.query(Habit).filter(Habit.user_id == user_id).all()
    habit_ids = [h.id for h in habits]
    
    total_logs = db.query(HabitLog).filter(
        HabitLog.habit_id.in_(habit_ids),
        HabitLog.completed == 1,
    ).count()
    
    today = date.today()
    today_completed = db.query(HabitLog).filter(
        HabitLog.habit_id.in_(habit_ids),
        HabitLog.date == today,
        HabitLog.completed == 1,
    ).count()
    
    week_start = today - timedelta(days=today.weekday())
    week_completed = db.query(HabitLog).filter(
        HabitLog.habit_id.in_(habit_ids),
        HabitLog.date >= week_start,
        HabitLog.completed == 1,
    ).count()
    
    max_streak = 0
    for habit in habits:
        streak = 0
        check_date = today
        
        log_today = db.query(HabitLog).filter(
            HabitLog.habit_id == habit.id,
            HabitLog.date == today,
            HabitLog.completed == 1,
        ).first()
        
        if not log_today:
            check_date = today - timedelta(days=1)
        
        while True:
            log = db.query(HabitLog).filter(
                HabitLog.habit_id == habit.id,
                HabitLog.date == check_date,
                HabitLog.completed == 1,
            ).first()
            if log:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break
        
        if streak > max_streak:
            max_streak = streak
    
    return {
        "total_habits": len(habits),
        "total_completions": total_logs,
        "today_completed": today_completed,
        "week_completed": week_completed,
        "max_streak": max_streak,
    }
