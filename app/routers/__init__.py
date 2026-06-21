from app.routers.auth import router as auth_router
from app.routers.habits import router as habits_router
from app.routers.habit_logs import router as habit_logs_router
from app.routers.challenges import router as challenges_router
from app.routers.stats import router as stats_router

__all__ = ["auth", "habits", "habit_logs", "challenges", "stats"]
