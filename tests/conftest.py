import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.models import User, Habit, HabitLog, Challenge
from app.schemas import UserCreate, HabitCreate, ChallengeCreate
from app.services.auth_service import create_user, create_access_token
from app.services.habit_service import create_habit
from app.services.challenge_service import create_challenge
from app.services.habit_log_service import toggle_habit_log
from app.main import app

TEST_DATABASE_URL = "sqlite:///./test_habit_tracker.db"

engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_user(db):
    user = create_user(db, UserCreate(username="testuser", password="testpass123"))
    return user


@pytest.fixture(scope="function")
def test_user2(db):
    user = create_user(db, UserCreate(username="testuser2", password="testpass123"))
    return user


@pytest.fixture(scope="function")
def auth_token(test_user):
    return create_access_token(data={"sub": test_user.username})


@pytest.fixture(scope="function")
def client(db, auth_token):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        c.headers = {"Authorization": f"Bearer {auth_token}"}
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def test_habit(db, test_user):
    habit_create = HabitCreate(
        name="早起",
        description="每天早上7点起床",
        category="健康",
        frequency_type="daily",
        frequency_count=1,
    )
    return create_habit(db, habit_create, test_user.id)


@pytest.fixture
def test_habits(db, test_user):
    habit1 = create_habit(db, HabitCreate(
        name="早起", category="健康", frequency_type="daily", frequency_count=1,
    ), test_user.id)
    habit2 = create_habit(db, HabitCreate(
        name="阅读", category="学习", frequency_type="daily", frequency_count=1,
    ), test_user.id)
    habit3 = create_habit(db, HabitCreate(
        name="运动", category="健康", frequency_type="weekly", frequency_count=3,
    ), test_user.id)
    return [habit1, habit2, habit3]


@pytest.fixture
def test_challenge(db, test_user, test_habit):
    today = date.today()
    challenge_create = ChallengeCreate(
        habit_id=test_habit.id,
        name="30天早起挑战",
        target_days=30,
        start_date=today,
    )
    return create_challenge(db, challenge_create, test_user.id)


def create_logs_for_days(db, habit_id, user_id, dates, notes=None):
    notes = notes or [""] * len(dates)
    for i, d in enumerate(dates):
        toggle_habit_log(db, habit_id, user_id, d, notes[i])


def create_consecutive_logs(db, habit_id, user_id, start_date, num_days):
    dates = [start_date + timedelta(days=i) for i in range(num_days)]
    create_logs_for_days(db, habit_id, user_id, dates)
    return dates
