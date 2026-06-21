from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import Stats30DayTrend, StatsCategoryBreakdown, StatsMonthlyRate
from app.services import (
    get_current_user,
    get_30day_trend,
    get_category_breakdown,
    get_monthly_completion_rates,
    get_habit_monthly_rates,
    get_overall_stats,
)

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overall")
def overall_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_overall_stats(db, current_user.id)


@router.get("/30day-trend", response_model=List[Stats30DayTrend])
def trend_30day(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_30day_trend(db, current_user.id)


@router.get("/category-breakdown", response_model=List[StatsCategoryBreakdown])
def category_breakdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_category_breakdown(db, current_user.id)


@router.get("/monthly-rates", response_model=List[StatsMonthlyRate])
def monthly_rates(
    habit_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if habit_id:
        return get_habit_monthly_rates(db, habit_id, current_user.id)
    return get_monthly_completion_rates(db, current_user.id)
