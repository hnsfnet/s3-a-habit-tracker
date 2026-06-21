import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient


class TestHabitsAPI:
    def test_list_habits_empty(self, client):
        response = client.get("/api/habits/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_create_habit_success(self, client):
        payload = {
            "name": "早起",
            "description": "每天7点起床",
            "category": "健康",
            "frequency_type": "daily",
            "frequency_count": 1,
        }
        response = client.post("/api/habits/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "早起"
        assert data["category"] == "健康"
        assert data["frequency_type"] == "daily"
        assert "id" in data

    def test_create_habit_weekly(self, client):
        payload = {
            "name": "健身",
            "category": "运动",
            "frequency_type": "weekly",
            "frequency_count": 3,
        }
        response = client.post("/api/habits/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["frequency_type"] == "weekly"
        assert data["frequency_count"] == 3

    def test_list_habits_with_data(self, client):
        client.post("/api/habits/", json={
            "name": "习惯1", "category": "健康",
            "frequency_type": "daily", "frequency_count": 1,
        })
        client.post("/api/habits/", json={
            "name": "习惯2", "category": "学习",
            "frequency_type": "daily", "frequency_count": 1,
        })
        response = client.get("/api/habits/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_habit_by_id(self, client):
        create_resp = client.post("/api/habits/", json={
            "name": "查单个", "category": "健康",
            "frequency_type": "daily", "frequency_count": 1,
        })
        habit_id = create_resp.json()["id"]

        response = client.get(f"/api/habits/{habit_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == habit_id
        assert data["name"] == "查单个"
        assert "current_streak" in data
        assert "total_completed" in data
        assert "completion_rate" in data

    def test_get_habit_not_found(self, client):
        response = client.get("/api/habits/9999")
        assert response.status_code == 404

    def test_update_habit(self, client):
        create_resp = client.post("/api/habits/", json={
            "name": "原名", "category": "健康",
            "frequency_type": "daily", "frequency_count": 1,
        })
        habit_id = create_resp.json()["id"]

        update_resp = client.put(f"/api/habits/{habit_id}", json={
            "name": "新名", "description": "新描述"
        })
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["name"] == "新名"
        assert data["description"] == "新描述"

    def test_update_habit_not_found(self, client):
        response = client.put("/api/habits/9999", json={"name": "x"})
        assert response.status_code == 404

    def test_delete_habit(self, client):
        create_resp = client.post("/api/habits/", json={
            "name": "将删除", "category": "健康",
            "frequency_type": "daily", "frequency_count": 1,
        })
        habit_id = create_resp.json()["id"]

        delete_resp = client.delete(f"/api/habits/{habit_id}")
        assert delete_resp.status_code == 200

        get_resp = client.get(f"/api/habits/{habit_id}")
        assert get_resp.status_code == 404

    def test_delete_habit_not_found(self, client):
        response = client.delete("/api/habits/9999")
        assert response.status_code == 404

    def test_unauthorized_no_token(self):
        from app.main import app
        from fastapi.testclient import TestClient
        with TestClient(app) as c:
            response = c.get("/api/habits/")
            assert response.status_code == 401


class TestCheckinAPI:
    def test_checkin_success(self, client, test_habit, test_user):
        habit_id = test_habit.id
        today = date.today().isoformat()
        response = client.post(
            f"/api/habit-logs/toggle/{habit_id}",
            params={"log_date": today, "note": "测试打卡"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is True

    def test_checkin_undo(self, client, test_habit, test_user):
        habit_id = test_habit.id
        today = date.today().isoformat()
        client.post(f"/api/habit-logs/toggle/{habit_id}", params={"log_date": today})
        response = client.post(f"/api/habit-logs/toggle/{habit_id}", params={"log_date": today})
        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is False

    def test_checkin_future_date(self, client, test_habit, test_user):
        habit_id = test_habit.id
        future = (date.today() + timedelta(days=10)).isoformat()
        response = client.post(
            f"/api/habit-logs/toggle/{habit_id}",
            params={"log_date": future}
        )
        assert response.status_code == 200

    def test_checkin_get_date_logs(self, client, test_habits, test_user):
        habit1, habit2, habit3 = test_habits
        today = date.today().isoformat()
        client.post(f"/api/habit-logs/toggle/{habit1.id}", params={"log_date": today})
        client.post(f"/api/habit-logs/toggle/{habit2.id}", params={"log_date": today})

        response = client.get(f"/api/habit-logs/date/{today}")
        assert response.status_code == 200
        data = response.json()
        assert str(habit1.id) in data or habit1.id in data
        assert len(data) >= 2

    def test_checkin_weekly_stats(self, client, test_habit, test_user):
        habit_id = test_habit.id
        today = date.today()
        for i in range(3):
            d = (today - timedelta(days=i)).isoformat()
            client.post(f"/api/habit-logs/toggle/{habit_id}", params={"log_date": d})

        response = client.get("/api/habit-logs/weekly")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        total = sum(data.values())
        assert total >= 3


class TestStatsAPI:
    def test_overall_stats_empty(self, client):
        response = client.get("/api/stats/overall")
        assert response.status_code == 200
        data = response.json()
        assert data["total_habits"] == 0
        assert data["total_completions"] == 0
        assert data["today_completed"] == 0
        assert data["week_completed"] == 0
        assert data["max_streak"] == 0

    def test_overall_stats_with_data(self, client, test_habits, test_user):
        habit1, habit2, habit3 = test_habits
        today = date.today()
        for i in range(7):
            d = today - timedelta(days=i)
            client.post(f"/api/habit-logs/toggle/{habit1.id}", params={"log_date": d.isoformat()})
        client.post(f"/api/habit-logs/toggle/{habit2.id}", params={"log_date": today.isoformat()})

        response = client.get("/api/stats/overall")
        assert response.status_code == 200
        data = response.json()
        assert data["total_habits"] == 3
        assert data["today_completed"] >= 2
        assert data["max_streak"] >= 7

    def test_30day_trend_empty(self, client):
        response = client.get("/api/stats/30day-trend")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 30
        for item in data:
            assert "date" in item
            assert "count" in item
            assert isinstance(item["count"], int)

    def test_30day_trend_format(self, client, test_habit, test_user):
        habit_id = test_habit.id
        today = date.today()
        for i in range(5):
            d = (today - timedelta(days=i)).isoformat()
            client.post(f"/api/habit-logs/toggle/{habit_id}", params={"log_date": d})

        response = client.get("/api/stats/30day-trend")
        assert response.status_code == 200
        data = response.json()
        assert data[-1]["count"] >= 1

    def test_category_breakdown_empty(self, client):
        response = client.get("/api/stats/category-breakdown")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_category_breakdown_with_data(self, client, test_habits, test_user):
        habit1, habit2, habit3 = test_habits
        today = date.today().isoformat()
        client.post(f"/api/habit-logs/toggle/{habit1.id}", params={"log_date": today})
        client.post(f"/api/habit-logs/toggle/{habit2.id}", params={"log_date": today})
        client.post(f"/api/habit-logs/toggle/{habit3.id}", params={"log_date": today})

        response = client.get("/api/stats/category-breakdown")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        categories = [item["category"] for item in data]
        assert "健康" in categories

    def test_monthly_rates_empty(self, client):
        response = client.get("/api/stats/monthly-rates")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 6
        for item in data:
            assert "month" in item
            assert "rate" in item
            assert 0 <= item["rate"] <= 100


class TestChallengesAPI:
    def test_list_challenges_empty(self, client):
        response = client.get("/api/challenges/")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_create_challenge_success(self, client, test_habit):
        today = date.today().isoformat()
        payload = {
            "habit_id": test_habit.id,
            "name": "API测试挑战",
            "target_days": 21,
            "start_date": today,
        }
        response = client.post("/api/challenges/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "API测试挑战"
        assert data["target_days"] == 21
        assert data["is_completed"] is False
        assert "current_progress" in data
        assert "progress_percent" in data

    def test_create_challenge_invalid_habit(self, client):
        payload = {
            "habit_id": 9999,
            "name": "无效习惯挑战",
            "target_days": 7,
            "start_date": date.today().isoformat(),
        }
        response = client.post("/api/challenges/", json=payload)
        assert response.status_code == 400

    def test_get_challenge_by_id(self, client, test_challenge):
        response = client.get(f"/api/challenges/{test_challenge.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_challenge.id
        assert data["name"] == "30天早起挑战"
        assert "current_progress" in data

    def test_get_challenge_not_found(self, client):
        response = client.get("/api/challenges/9999")
        assert response.status_code == 404

    def test_update_challenge(self, client, test_challenge):
        response = client.put(
            f"/api/challenges/{test_challenge.id}",
            json={"name": "改名了"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "改名了"

    def test_update_challenge_not_found(self, client):
        response = client.put("/api/challenges/9999", json={"name": "x"})
        assert response.status_code == 404

    def test_delete_challenge(self, client, test_challenge):
        delete_resp = client.delete(f"/api/challenges/{test_challenge.id}")
        assert delete_resp.status_code == 200

        get_resp = client.get(f"/api/challenges/{test_challenge.id}")
        assert get_resp.status_code == 404

    def test_delete_challenge_not_found(self, client):
        response = client.delete("/api/challenges/9999")
        assert response.status_code == 404

    def test_challenge_progress_updates_with_checkins(
        self, client, test_habit, test_user
    ):
        today = date.today()
        start = today - timedelta(days=4)
        payload = {
            "habit_id": test_habit.id,
            "name": "进度测试",
            "target_days": 5,
            "start_date": start.isoformat(),
        }
        create_resp = client.post("/api/challenges/", json=payload)
        challenge_id = create_resp.json()["id"]

        for i in range(4):
            d = (start + timedelta(days=i)).isoformat()
            client.post(
                f"/api/habit-logs/toggle/{test_habit.id}",
                params={"log_date": d}
            )

        response = client.get(f"/api/challenges/{challenge_id}")
        data = response.json()
        assert data["current_progress"] == 4
        assert data["progress_percent"] == pytest.approx(80.0, abs=0.1)

    def test_monthly_rates_with_habit_filter(self, client, test_habits, test_user):
        habit1, habit2, _ = test_habits
        today = date.today().isoformat()
        client.post(f"/api/habit-logs/toggle/{habit1.id}", params={"log_date": today})
        client.post(f"/api/habit-logs/toggle/{habit1.id}", params={
            "log_date": (date.today() - timedelta(days=1)).isoformat()
        })

        response = client.get(f"/api/stats/monthly-rates?habit_id={habit1.id}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 6
