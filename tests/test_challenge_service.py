import pytest
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.models import Challenge
from app.schemas import ChallengeCreate, ChallengeUpdate
from app.services.challenge_service import (
    create_challenge,
    get_challenges_by_user,
    get_challenge_by_id,
    update_challenge,
    delete_challenge,
    calculate_challenge_progress,
    get_challenges_with_stats,
    get_active_challenge_for_habit,
)
from app.services.habit_log_service import toggle_habit_log


class TestCreateChallenge:
    def test_create_challenge_success(self, db, test_habit, test_user):
        today = date.today()
        challenge = create_challenge(db, ChallengeCreate(
            habit_id=test_habit.id,
            name="21天早起挑战",
            target_days=21,
            start_date=today,
        ), test_user.id)

        assert challenge is not None
        assert challenge.id is not None
        assert challenge.habit_id == test_habit.id
        assert challenge.user_id == test_user.id
        assert challenge.name == "21天早起挑战"
        assert challenge.target_days == 21
        assert challenge.start_date == today
        assert challenge.end_date == today + timedelta(days=20)
        assert challenge.is_completed is False
        assert challenge.completed_date is None

    def test_challenge_end_date_calculated_correctly(self, db, test_habit, test_user):
        start = date(2025, 1, 1)
        challenge = create_challenge(db, ChallengeCreate(
            habit_id=test_habit.id,
            name="7天挑战",
            target_days=7,
            start_date=start,
        ), test_user.id)
        assert challenge.end_date == date(2025, 1, 7)

    def test_create_challenge_invalid_habit(self, db, test_user):
        challenge = create_challenge(db, ChallengeCreate(
            habit_id=9999,
            name="无效挑战",
            target_days=7,
            start_date=date.today(),
        ), test_user.id)
        assert challenge is None

    def test_create_challenge_other_user_habit(self, db, test_habit, test_user2):
        challenge = create_challenge(db, ChallengeCreate(
            habit_id=test_habit.id,
            name="越权挑战",
            target_days=7,
            start_date=date.today(),
        ), test_user2.id)
        assert challenge is None


class TestGetChallenges:
    def test_empty_user_no_challenges(self, db, test_user):
        challenges = get_challenges_by_user(db, test_user.id)
        assert challenges == []

    def test_user_with_challenges(self, db, test_habit, test_user):
        for i in range(3):
            create_challenge(db, ChallengeCreate(
                habit_id=test_habit.id,
                name=f"挑战{i}",
                target_days=7 + i,
                start_date=date.today(),
            ), test_user.id)

        challenges = get_challenges_by_user(db, test_user.id)
        assert len(challenges) == 3

    def test_get_challenge_by_id(self, db, test_challenge, test_user):
        challenge = get_challenge_by_id(db, test_challenge.id, test_user.id)
        assert challenge is not None
        assert challenge.id == test_challenge.id
        assert challenge.name == "30天早起挑战"

    def test_get_challenge_not_found(self, db, test_user):
        challenge = get_challenge_by_id(db, 9999, test_user.id)
        assert challenge is None

    def test_other_user_cannot_get(self, db, test_challenge, test_user2):
        challenge = get_challenge_by_id(db, test_challenge.id, test_user2.id)
        assert challenge is None


class TestUpdateChallenge:
    def test_update_challenge_name(self, db, test_challenge, test_user):
        updated = update_challenge(
            db,
            test_challenge.id,
            ChallengeUpdate(name="新挑战名字"),
            test_user.id,
        )
        assert updated.name == "新挑战名字"

    def test_update_unknown_field_ignored(self, db, test_challenge, test_user):
        old_target = test_challenge.target_days
        updated = update_challenge(
            db,
            test_challenge.id,
            ChallengeUpdate(name="改名不改目标"),
            test_user.id,
        )
        assert updated.name == "改名不改目标"
        assert updated.target_days == old_target

    def test_update_nonexistent_challenge(self, db, test_user):
        result = update_challenge(db, 9999, ChallengeUpdate(name="x"), test_user.id)
        assert result is None

    def test_other_user_cannot_update(self, db, test_challenge, test_user2):
        result = update_challenge(db, test_challenge.id, ChallengeUpdate(name="x"), test_user2.id)
        assert result is None


class TestDeleteChallenge:
    def test_delete_success(self, db, test_challenge, test_user):
        result = delete_challenge(db, test_challenge.id, test_user.id)
        assert result is True
        assert get_challenge_by_id(db, test_challenge.id, test_user.id) is None

    def test_delete_not_found(self, db, test_user):
        result = delete_challenge(db, 9999, test_user.id)
        assert result is False

    def test_other_user_cannot_delete(self, db, test_challenge, test_user2):
        result = delete_challenge(db, test_challenge.id, test_user2.id)
        assert result is False
        assert get_challenge_by_id(db, test_challenge.id, test_challenge.user_id) is not None


class TestCalculateProgress:
    def test_new_challenge_zero_progress(self, db, test_challenge, test_user):
        stats = calculate_challenge_progress(db, test_challenge)
        assert stats.current_progress == 0
        assert stats.current_streak == 0
        assert stats.progress_percent == 0.0
        assert stats.is_completed is False

    def test_partial_progress(self, db, test_habit, test_user):
        start = date.today() - timedelta(days=10)
        challenge = create_challenge(db, ChallengeCreate(
            habit_id=test_habit.id,
            name="部分进度测试",
            target_days=30,
            start_date=start,
        ), test_user.id)

        today = date.today()
        for i in range(5):
            toggle_habit_log(db, test_habit.id, test_user.id, today - timedelta(days=i))

        stats = calculate_challenge_progress(db, challenge)
        assert stats.current_progress == 5
        assert stats.current_streak == 5
        assert stats.progress_percent == pytest.approx((5 / 30) * 100, abs=0.1)

    def test_complete_challenge(self, db, test_habit, test_user):
        start = date.today() - timedelta(days=6)
        challenge = create_challenge(db, ChallengeCreate(
            habit_id=test_habit.id,
            name="7天挑战",
            target_days=7,
            start_date=start,
        ), test_user.id)

        for i in range(7):
            toggle_habit_log(db, test_habit.id, test_user.id, start + timedelta(days=i))

        stats = calculate_challenge_progress(db, challenge)
        assert stats.current_progress == 7
        assert stats.progress_percent == 100.0
        assert stats.is_completed is True
        assert stats.completed_date is not None

    def test_expired_challenge_remaining_zero(self, db, test_habit, test_user):
        start = date.today() - timedelta(days=30)
        challenge = create_challenge(db, ChallengeCreate(
            habit_id=test_habit.id,
            name="过期挑战",
            target_days=5,
            start_date=start,
        ), test_user.id)

        stats = calculate_challenge_progress(db, challenge)
        assert stats.remaining_days == 0

    def test_progress_streak_calculation(self, db, test_habit, test_user):
        start = date.today() - timedelta(days=10)
        challenge = create_challenge(db, ChallengeCreate(
            habit_id=test_habit.id,
            name="连续测试",
            target_days=15,
            start_date=start,
        ), test_user.id)

        today = date.today()
        for i in range(3):
            toggle_habit_log(db, test_habit.id, test_user.id, today - timedelta(days=i))
        toggle_habit_log(db, test_habit.id, test_user.id, today - timedelta(days=5))

        stats = calculate_challenge_progress(db, challenge)
        assert stats.current_progress == 4
        assert stats.current_streak == 3

    def test_completed_date_set_to_actual_day(self, db, test_habit, test_user):
        start = date(2025, 6, 1)
        challenge = create_challenge(db, ChallengeCreate(
            habit_id=test_habit.id,
            name="完成日期测试",
            target_days=30,
            start_date=start,
        ), test_user.id)

        log_dates = [date(2025, 6, 1), date(2025, 6, 3), date(2025, 6, 5), date(2025, 6, 7), date(2025, 6, 9)]
        for d in log_dates:
            toggle_habit_log(db, test_habit.id, test_user.id, d)

        stats = calculate_challenge_progress(db, challenge)
        assert stats.current_progress == 5
        assert stats.progress_percent > 0.0

    def test_already_completed_idempotent(self, db, test_habit, test_user):
        start = date.today() - timedelta(days=6)
        challenge = create_challenge(db, ChallengeCreate(
            habit_id=test_habit.id,
            name="幂等测试",
            target_days=3,
            start_date=start,
        ), test_user.id)

        for i in range(5):
            toggle_habit_log(db, test_habit.id, test_user.id, start + timedelta(days=i))

        stats1 = calculate_challenge_progress(db, challenge)
        stats2 = calculate_challenge_progress(db, challenge)

        assert stats1.is_completed is True
        assert stats2.is_completed is True
        assert stats1.completed_date == stats2.completed_date


class TestActiveChallenge:
    def test_active_challenge_found(self, db, test_challenge, test_habit, test_user):
        active = get_active_challenge_for_habit(db, test_habit.id, test_user.id)
        assert active is not None
        assert active.id == test_challenge.id

    def test_expired_challenge_not_active(self, db, test_habit, test_user):
        start = date.today() - timedelta(days=40)
        challenge = create_challenge(db, ChallengeCreate(
            habit_id=test_habit.id,
            name="已过期",
            target_days=5,
            start_date=start,
        ), test_user.id)

        active = get_active_challenge_for_habit(db, test_habit.id, test_user.id)
        assert active is None

    def test_future_challenge_not_active(self, db, test_habit, test_user):
        future = date.today() + timedelta(days=10)
        challenge = create_challenge(db, ChallengeCreate(
            habit_id=test_habit.id,
            name="未开始",
            target_days=30,
            start_date=future,
        ), test_user.id)

        active = get_active_challenge_for_habit(db, test_habit.id, test_user.id)
        assert active is None

    def test_completed_challenge_not_active(self, db, test_habit, test_user):
        start = date.today() - timedelta(days=10)
        challenge = create_challenge(db, ChallengeCreate(
            habit_id=test_habit.id,
            name="已完成",
            target_days=5,
            start_date=start,
        ), test_user.id)

        for i in range(5):
            toggle_habit_log(db, test_habit.id, test_user.id, start + timedelta(days=i))

        calculate_challenge_progress(db, challenge)

        active = get_active_challenge_for_habit(db, test_habit.id, test_user.id)
        assert active is None


class TestGetChallengesWithStats:
    def test_empty_user(self, db, test_user):
        result = get_challenges_with_stats(db, test_user.id)
        assert result == []

    def test_with_challenges(self, db, test_challenge, test_user):
        result = get_challenges_with_stats(db, test_user.id)
        assert len(result) == 1
        assert hasattr(result[0], "current_progress")
        assert hasattr(result[0], "progress_percent")
