import pytest
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.models import Habit, HabitLog, Challenge
from app.schemas import HabitCreate, HabitUpdate
from app.services.habit_service import (
    get_habits_by_user,
    get_habit_by_id,
    create_habit,
    update_habit,
    delete_habit,
)
from app.services.habit_log_service import (
    toggle_habit_log,
    get_user_logs_for_date,
)
from app.services.challenge_service import create_challenge
from app.schemas import ChallengeCreate
from tests.conftest import create_consecutive_logs


class TestGetHabitsByUser:
    def test_empty_user_no_habits(self, db, test_user):
        habits = get_habits_by_user(db, test_user.id)
        assert habits == []

    def test_user_with_multiple_habits(self, db, test_habits, test_user):
        habits = get_habits_by_user(db, test_user.id)
        assert len(habits) == 3
        habit_names = {h.name for h in habits}
        assert "早起" in habit_names
        assert "阅读" in habit_names
        assert "运动" in habit_names

    def test_isolate_between_users(self, db, test_user, test_user2, test_habit):
        habits_user1 = get_habits_by_user(db, test_user.id)
        habits_user2 = get_habits_by_user(db, test_user2.id)
        assert len(habits_user1) == 1
        assert len(habits_user2) == 0


class TestGetHabitById:
    def test_get_existing_habit(self, db, test_habit, test_user):
        habit = get_habit_by_id(db, test_habit.id, test_user.id)
        assert habit is not None
        assert habit.id == test_habit.id
        assert habit.name == "早起"

    def test_get_nonexistent_habit(self, db, test_user):
        habit = get_habit_by_id(db, 9999, test_user.id)
        assert habit is None

    def test_other_user_cannot_access(self, db, test_habit, test_user2):
        habit = get_habit_by_id(db, test_habit.id, test_user2.id)
        assert habit is None


class TestCreateHabit:
    def test_create_habit_normal(self, db, test_user):
        habit_create = HabitCreate(
            name="早睡",
            description="每天11点前睡觉",
            category="健康",
            frequency_type="daily",
            frequency_count=1,
        )
        habit = create_habit(db, habit_create, test_user.id)
        assert habit.id is not None
        assert habit.name == "早睡"
        assert habit.category == "健康"
        assert habit.user_id == test_user.id

    def test_create_habit_with_weekly_frequency(self, db, test_user):
        habit_create = HabitCreate(
            name="健身房",
            category="运动",
            frequency_type="weekly",
            frequency_count=3,
        )
        habit = create_habit(db, habit_create, test_user.id)
        assert habit.frequency_type == "weekly"
        assert habit.frequency_count == 3

    def test_create_multiple_habits_same_name_allowed(self, db, test_user):
        habit1 = create_habit(db, HabitCreate(
            name="习惯A", category="测试", frequency_type="daily"
        ), test_user.id)
        habit2 = create_habit(db, HabitCreate(
            name="习惯A", category="测试", frequency_type="daily"
        ), test_user.id)
        assert habit1.id != habit2.id

    def test_create_habit_empty_name_exception(self, db, test_user):
        from app.schemas import HabitCreate as HC
        with pytest.raises(Exception):
            HC(
                name=None,
                category="测试",
                frequency_type="daily",
            )
        habit = create_habit(db, HC(
            name="", category="测试", frequency_type="daily"
        ), test_user.id)
        assert habit.name == ""


class TestUpdateHabit:
    def test_update_habit_name(self, db, test_habit, test_user):
        updated = update_habit(
            db,
            test_habit.id,
            HabitUpdate(name="早起打卡"),
            test_user.id,
        )
        assert updated.name == "早起打卡"

    def test_update_habit_multiple_fields(self, db, test_habit, test_user):
        updated = update_habit(
            db,
            test_habit.id,
            HabitUpdate(
                name="新名称",
                description="新描述",
                category="生活",
                frequency_type="weekly",
                frequency_count=2,
            ),
            test_user.id,
        )
        assert updated.name == "新名称"
        assert updated.description == "新描述"
        assert updated.category == "生活"
        assert updated.frequency_type == "weekly"
        assert updated.frequency_count == 2

    def test_update_partial_field(self, db, test_habit, test_user):
        old_name = test_habit.name
        old_category = test_habit.category
        updated = update_habit(
            db,
            test_habit.id,
            HabitUpdate(description="仅更新描述"),
            test_user.id,
        )
        assert updated.name == old_name
        assert updated.category == old_category
        assert updated.description == "仅更新描述"

    def test_update_nonexistent_habit(self, db, test_user):
        result = update_habit(db, 9999, HabitUpdate(name="x"), test_user.id)
        assert result is None

    def test_other_user_cannot_update(self, db, test_habit, test_user2):
        result = update_habit(db, test_habit.id, HabitUpdate(name="x"), test_user2.id)
        assert result is None


class TestDeleteHabitCascade:
    def test_delete_existing_habit(self, db, test_habit, test_user):
        result = delete_habit(db, test_habit.id, test_user.id)
        assert result is True
        assert get_habit_by_id(db, test_habit.id, test_user.id) is None

    def test_delete_nonexistent_habit(self, db, test_user):
        result = delete_habit(db, 9999, test_user.id)
        assert result is False

    def test_other_user_cannot_delete(self, db, test_habit, test_user2):
        result = delete_habit(db, test_habit.id, test_user2.id)
        assert result is False
        assert get_habit_by_id(db, test_habit.id, test_habit.user_id) is not None

    def test_delete_cascades_habit_logs(self, db, test_habit, test_user):
        today = date.today()
        for i in range(5):
            toggle_habit_log(db, test_habit.id, test_user.id, today - timedelta(days=i))
        assert db.query(HabitLog).filter(HabitLog.habit_id == test_habit.id).count() == 5

        delete_habit(db, test_habit.id, test_user.id)
        assert db.query(HabitLog).filter(HabitLog.habit_id == test_habit.id).count() == 0

    def test_delete_cascades_challenges(self, db, test_habit, test_user):
        challenge = create_challenge(db, ChallengeCreate(
            habit_id=test_habit.id,
            name="测试挑战",
            target_days=7,
            start_date=date.today(),
        ), test_user.id)
        assert challenge is not None
        assert db.query(Challenge).filter(Challenge.habit_id == test_habit.id).count() == 1

        delete_habit(db, test_habit.id, test_user.id)
        assert db.query(Challenge).filter(Challenge.habit_id == test_habit.id).count() == 0

    def test_delete_cascades_both_logs_and_challenges(self, db, test_habit, test_user):
        for i in range(3):
            toggle_habit_log(db, test_habit.id, test_user.id, date.today() - timedelta(days=i))
        create_challenge(db, ChallengeCreate(
            habit_id=test_habit.id, name="挑战1", target_days=30,
            start_date=date.today(),
        ), test_user.id)

        delete_habit(db, test_habit.id, test_user.id)
        assert db.query(HabitLog).filter(HabitLog.habit_id == test_habit.id).count() == 0
        assert db.query(Challenge).filter(Challenge.habit_id == test_habit.id).count() == 0


class TestToggleHabitLog:
    def test_checkin_success(self, db, test_habit, test_user):
        today = date.today()
        log = toggle_habit_log(db, test_habit.id, test_user.id, today)
        assert log is not None
        assert log.habit_id == test_habit.id
        assert log.date == today
        assert log.completed == 1

    def test_duplicate_checkin_undoes(self, db, test_habit, test_user):
        today = date.today()
        log1 = toggle_habit_log(db, test_habit.id, test_user.id, today)
        assert log1 is not None

        log2 = toggle_habit_log(db, test_habit.id, test_user.id, today)
        assert log2 is None

        logs = get_user_logs_for_date(db, test_user.id, today)
        assert test_habit.id not in logs

    def test_triple_toggle_rechecks(self, db, test_habit, test_user):
        today = date.today()
        toggle_habit_log(db, test_habit.id, test_user.id, today)
        toggle_habit_log(db, test_habit.id, test_user.id, today)
        log3 = toggle_habit_log(db, test_habit.id, test_user.id, today)
        assert log3 is not None

    def test_checkin_with_note(self, db, test_habit, test_user):
        today = date.today()
        log = toggle_habit_log(db, test_habit.id, test_user.id, today, "今天状态很好")
        assert log.note == "今天状态很好"

    def test_checkin_multiple_days(self, db, test_habit, test_user):
        today = date.today()
        dates = [today - timedelta(days=i) for i in range(7)]
        for d in dates:
            log = toggle_habit_log(db, test_habit.id, test_user.id, d)
            assert log is not None

        count = db.query(HabitLog).filter(HabitLog.habit_id == test_habit.id).count()
        assert count == 7

    def test_checkin_future_date_allowed(self, db, test_habit, test_user):
        future = date.today() + timedelta(days=5)
        log = toggle_habit_log(db, test_habit.id, test_user.id, future)
        assert log is not None

    def test_checkin_wrong_user_habit(self, db, test_habit, test_user2):
        log = toggle_habit_log(db, test_habit.id, test_user2.id, date.today())
        assert log is None

    def test_checkin_with_note_skip_empty(self, db, test_habit, test_user):
        log = toggle_habit_log(db, test_habit.id, test_user.id, date.today(), "")
        assert log is not None
        assert log.note == ""
