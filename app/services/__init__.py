from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    get_user_by_username,
    create_user,
    authenticate_user,
    get_current_user,
)

from app.services.habit_service import (
    get_habits_by_user,
    get_habit_by_id,
    create_habit,
    update_habit,
    delete_habit,
    calculate_current_streak,
    calculate_total_completed,
    calculate_completion_rate,
    get_habits_with_stats,
)

from app.services.habit_log_service import (
    get_log_by_habit_and_date,
    toggle_habit_log,
    get_logs_for_date_range,
    get_user_logs_for_date,
    get_weekly_completion,
    get_monthly_completion,
    get_habit_logs_for_month,
)

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "get_user_by_username",
    "create_user",
    "authenticate_user",
    "get_current_user",
    "get_habits_by_user",
    "get_habit_by_id",
    "create_habit",
    "update_habit",
    "delete_habit",
    "calculate_current_streak",
    "calculate_total_completed",
    "calculate_completion_rate",
    "get_habits_with_stats",
    "get_log_by_habit_and_date",
    "toggle_habit_log",
    "get_logs_for_date_range",
    "get_user_logs_for_date",
    "get_weekly_completion",
    "get_monthly_completion",
    "get_habit_logs_for_month",
]
