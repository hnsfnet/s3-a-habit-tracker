from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List


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


class HabitLogCreate(HabitLogBase):
    pass


class HabitLogResponse(HabitLogBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
