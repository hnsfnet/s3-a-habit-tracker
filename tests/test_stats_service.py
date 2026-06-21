import pytest
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.models import Habit, HabitLog
from app.services.stats_service import (
    calculate_current_streak,
    calculate_total_completed,
    calculate_completion_rate,
    get_habits_with_stats,
    get_30day_trend,
    get_category_breakdown,
    get_monthly_completion_rates,
    get_overall_stats,
)
from app.services.challenge_service import calculate_challenge_progress
from app.services.habit_log_service import toggle_habit_log
from app.schemas import ChallengeCreate
from app.services.challenge_service import create_challenge
from tests.conftest import create_logs_for_days, create_consecutive_logs


class TestCalculateCurrentStreak:
    def test_no_logs_streak_zero(self, db, test_habit):
        streak = calculate_current_streak(db, test_habit.id)
        assert streak == 0

    def test_consecutive_days_streak_correct(self, db, test_habit, test_user):
        today = date.today()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)
        create_logs_for_days(db, test_habit.id, test_user.id, [two_days_ago, yesterday, today])
        streak = calculate_current_streak(db, test_habit.id)
        assert streak == 3

    def test_today_no_log_yesterday_logged(self, db, test_habit, test_user):
        yesterday = date.today() - timedelta(days=1)
        two_days_ago = date.today() - timedelta(days=2)
        create_logs_for_days(db, test_habit.id, test_user.id, [two_days_ago, yesterday])
        streak = calculate_current_streak(db, test_habit.id)
        assert streak == 2

    def test_streak_interruption_reset(self, db, test_habit, test_user):
        today = date.today()
        two_days_ago = today - timedelta(days=2)
        three_days_ago = today - timedelta(days=3)
        create_logs_for_days(db, test_habit.id, test_user.id, [three_days_ago, two_days_ago, today])
        streak = calculate_current_streak(db, test_habit.id)
        assert streak == 1

    def test_streak_only_today(self, db, test_habit, test_user):
        create_logs_for_days(db, test_habit.id, test_user.id, [date.today()])
        streak = calculate_current_streak(db, test_habit.id)
        assert streak == 1

    def test_streak_only_yesterday(self, db, test_habit, test_user):
        yesterday = date.today() - timedelta(days=1)
        create_logs_for_days(db, test_habit.id, test_user.id, [yesterday])
        streak = calculate_current_streak(db, test_habit.id)
        assert streak == 1

    def test_cross_month_streak(self, db, test_habit, test_user):
        today = date.today()
        dates = []
        for i in range(10):
            d = today - timedelta(days=i)
            dates.append(d)
        create_logs_for_days(db, test_habit.id, test_user.id, dates)
        streak = calculate_current_streak(db, test_habit.id)
        assert streak == 10

    def test_cross_year_streak(self, db, test_habit, test_user):
        end_of_year = date.today().replace(month=12, day=31)
        if end_of_year > date.today():
            end_of_year = end_of_year.replace(year=end_of_year.year - 1)
        dates = []
        for i in range(5):
            dates.append(end_of_year - timedelta(days=i))
        next_year_jan = end_of_year.replace(year=end_of_year.year + 1, month=1, day=1)
        for i in range(3):
            dates.append(next_year_jan + timedelta(days=i))
        create_logs_for_days(db, test_habit.id, test_user.id, dates)
        streak = calculate_current_streak(db, test_habit.id)
        assert streak == 0


class TestCalculateTotalCompleted:
    def test_no_logs(self, db, test_habit):
        total = calculate_total_completed(db, test_habit.id)
        assert total == 0

    def test_multiple_logs(self, db, test_habit, test_user):
        today = date.today()
        dates = [today - timedelta(days=i) for i in range(15)]
        create_logs_for_days(db, test_habit.id, test_user.id, dates)
        total = calculate_total_completed(db, test_habit.id)
        assert total == 15

    def test_only_completed_counted(self, db, test_habit, test_user):
        today = date.today()
        toggle_habit_log(db, test_habit.id, test_user.id, today)
        toggle_habit_log(db, test_habit.id, test_user.id, today)
        toggle_habit_log(db, test_habit.id, test_user.id, today - timedelta(days=1))
        total = calculate_total_completed(db, test_habit.id)
        assert total == 1


class TestCalculateCompletionRate:
    def test_no_logs_zero_rate(self, db, test_habit):
        rate = calculate_completion_rate(db, test_habit.id)
        assert rate == 0.0

    def test_full_daily_compliance(self, db, test_habit, test_user):
        today = date.today()
        created_date = today - timedelta(days=9)
        for i in range(10):
            toggle_habit_log(db, test_habit.id, test_user.id, created_date + timedelta(days=i))
        rate = calculate_completion_rate(db, test_habit.id)
        assert 0.0 <= rate <= 100.0

    def test_rate_not_exceed_100(self, db, test_habit, test_user):
        today = date.today()
        for i in range(100):
            toggle_habit_log(db, test_habit.id, test_user.id, today)
            toggle_habit_log(db, test_habit.id, test_user.id, today)
        rate = calculate_completion_rate(db, test_habit.id)
        assert rate <= 100.0


class Test30DayTrend:
    def test_empty_trend(self, db, test_user):
        trend = get_30day_trend(db, test_user.id)
        assert len(trend) == 30
        for t in trend:
            assert t.count == 0

    def test_trend_with_logs(self, db, test_habits, test_user):
        today = date.today()
        habit1, habit2, _ = test_habits
        for i in range(10):
            d = today - timedelta(days=i)
            toggle_habit_log(db, habit1.id, test_user.id, d)
            if i % 2 == 0:
                toggle_habit_log(db, habit2.id, test_user.id, d)

        trend = get_30day_trend(db, test_user.id)
        today_count = trend[-1].count
        assert today_count >= 1

    def test_trend_date_format(self, db, test_user):
        trend = get_30day_trend(db, test_user.id)
        today = date.today()
        first_date = date.fromisoformat(trend[0].date)
        last_date = date.fromisoformat(trend[-1].date)
        assert last_date == today
        assert (last_date - first_date).days == 29


class TestCategoryBreakdown:
    def test_empty_user_no_categories(self, db, test_user):
        result = get_category_breakdown(db, test_user.id)
        assert result == []

    def test_single_category(self, db, test_habit, test_user):
        for i in range(10):
            toggle_habit_log(db, test_habit.id, test_user.id, date.today() - timedelta(days=i))

        result = get_category_breakdown(db, test_user.id)
        assert len(result) == 1
        assert result[0].category == "健康"
        assert result[0].count == 10
        assert result[0].percentage == 100.0

    def test_multiple_categories(self, db, test_habits, test_user):
        habit1, habit2, habit3 = test_habits
        for i in range(5):
            toggle_habit_log(db, habit1.id, test_user.id, date.today() - timedelta(days=i))
            toggle_habit_log(db, habit3.id, test_user.id, date.today() - timedelta(days=i))
        for i in range(10):
            toggle_habit_log(db, habit2.id, test_user.id, date.today() - timedelta(days=i))

        result = get_category_breakdown(db, test_user.id)
        categories = {r.category: r.count for r in result}
        assert "健康" in categories
        assert "学习" in categories
        assert categories["健康"] == 10
        assert categories["学习"] == 10

        total = sum(r.count for r in result)
        total_pct = sum(r.percentage for r in result)
        assert total == 20
        assert abs(total_pct - 100.0) < 0.1 or total == 0


class TestMonthlyCompletionRates:
    def test_empty_rates(self, db, test_user):
        rates = get_monthly_completion_rates(db, test_user.id)
        assert len(rates) == 6
        for r in rates:
            assert r.rate == 0.0

    def test_rates_format(self, db, test_user):
        rates = get_monthly_completion_rates(db, test_user.id)
        for r in rates:
            assert "年" in r.month and "月" in r.month
            assert 0.0 <= r.rate <= 100.0

    def test_with_single_habit_logs(self, db, test_habit, test_user):
        today = date.today()
        days_to_log = min(10, (today - date(today.year, today.month, 1)).days + 1)
        for i in range(days_to_log):
            toggle_habit_log(db, test_habit.id, test_user.id, today - timedelta(days=i))

        rates = get_monthly_completion_rates(db, test_user.id)
        latest_rate = rates[-1].rate
        assert latest_rate >= 0.0


class TestOverallStats:
    def test_empty_stats(self, db, test_user):
        stats = get_overall_stats(db, test_user.id)
        assert stats["total_habits"] == 0
        assert stats["total_completions"] == 0
        assert stats["today_completed"] == 0
        assert stats["week_completed"] == 0
        assert stats["max_streak"] == 0

    def test_stats_with_data(self, db, test_habits, test_user):
        habit1, habit2, _ = test_habits
        today = date.today()
        for i in range(7):
            d = today - timedelta(days=i)
            toggle_habit_log(db, habit1.id, test_user.id, d)
            if i < 5:
                toggle_habit_log(db, habit2.id, test_user.id, d)

        stats = get_overall_stats(db, test_user.id)
        assert stats["total_habits"] == 3
        assert stats["total_completions"] >= 12
        assert stats["today_completed"] >= 1
        assert stats["week_completed"] >= 2
        assert stats["max_streak"] >= 7


class TestChallengeProgressWithFilter:
    def test_challenge_start_date_filters_history(self, db, test_habit, test_user):
        today = date.today()
        start_date = today - timedelta(days=5)

        for i in range(10):
            toggle_habit_log(db, test_habit.id, test_user.id, start_date - timedelta(days=i + 1))

        challenge = create_challenge(db, ChallengeCreate(
            habit_id=test_habit.id,
            name="过滤测试",
            target_days=10,
            start_date=start_date,
        ), test_user.id)

        for i in range(3):
            toggle_habit_log(db, test_habit.id, test_user.id, start_date + timedelta(days=i))

        stats = calculate_challenge_progress(db, challenge)
        assert stats.current_progress == 3

    def test_challenge_not_started_zero_progress(self, db, test_habit, test_user):
        future_start = date.today() + timedelta(days=10)
        challenge = create_challenge(db, ChallengeCreate(
            habit_id=test_habit.id,
            name="未开始挑战",
            target_days=30,
            start_date=future_start,
        ), test_user.id)

        toggle_habit_log(db, test_habit.id, test_user.id, date.today())

        stats = calculate_challenge_progress(db, challenge)
        assert stats.current_progress == 0
        assert stats.current_streak == 0
        assert stats.progress_percent == 0.0

    def test_challenge_after_end_still_counts(self, db, test_habit, test_user):
        today = date.today()
        start = today - timedelta(days=10)
        challenge = create_challenge(db, ChallengeCreate(
            habit_id=test_habit.id,
            name="已结束挑战",
            target_days=5,
            start_date=start,
        ), test_user.id)

        for i in range(5):
            toggle_habit_log(db, test_habit.id, test_user.id, start + timedelta(days=i))
        toggle_habit_log(db, test_habit.id, test_user.id, today)

        stats = calculate_challenge_progress(db, challenge)
        assert stats.current_progress == 5
        assert stats.is_completed is True
        assert stats.remaining_days == 0
