from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List, Dict


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class UserLogin(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class HabitBase(BaseModel):
    name: str
    description: Optional[str] = ""
    category: str
    frequency_type: str
    frequency_count: int = 1


class HabitCreate(HabitBase):
    pass


class HabitUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    frequency_type: Optional[str] = None
    frequency_count: Optional[int] = None


class HabitResponse(HabitBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class HabitWithStats(HabitResponse):
    current_streak: int = 0
    total_completed: int = 0
    completion_rate: float = 0.0


class HabitLogBase(BaseModel):
    habit_id: int
    date: date
    completed: int = 1
    note: Optional[str] = ""


class HabitLogCreate(HabitLogBase):
    pass


class HabitLogUpdateNote(BaseModel):
    note: str


class HabitLogWithNote(HabitLogBase):
    id: int
    created_at: datetime
    note: str
    habit_name: Optional[str] = None

    class Config:
        from_attributes = True


class HabitLogResponse(HabitLogBase):
    id: int
    created_at: datetime
    note: str

    class Config:
        from_attributes = True


class ChallengeBase(BaseModel):
    habit_id: int
    name: str
    target_days: int
    start_date: date


class ChallengeCreate(ChallengeBase):
    pass


class ChallengeUpdate(BaseModel):
    name: Optional[str] = None
    target_days: Optional[int] = None


class ChallengeResponse(ChallengeBase):
    id: int
    user_id: int
    end_date: date
    is_completed: bool
    completed_date: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChallengeWithStats(ChallengeResponse):
    current_progress: int = 0
    current_streak: int = 0
    remaining_days: int = 0
    progress_percent: float = 0.0
    daily_status: Dict[str, bool] = {}
    habit_name: Optional[str] = None


class Stats30DayTrend(BaseModel):
    date: str
    count: int


class StatsCategoryBreakdown(BaseModel):
    category: str
    count: int
    percentage: float


class StatsMonthlyRate(BaseModel):
    month: str
    rate: float

