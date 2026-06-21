import requests
from datetime import date, timedelta

BASE_URL = "http://localhost:8000"
USERNAME = "testuser"
PASSWORD = "123456"

def get_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", data={
        "username": USERNAME,
        "password": PASSWORD
    })
    if r.status_code == 200:
        return r.json()["access_token"]
    r = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": USERNAME,
        "password": PASSWORD
    })
    if r.status_code == 200:
        return get_token()
    raise Exception(f"无法获取 token: {r.status_code} - {r.text}")


def toggle_log(token, habit_id, log_date, note=""):
    r = requests.post(
        f"{BASE_URL}/api/habit-logs/toggle/{habit_id}",
        params={"log_date": log_date.isoformat(), "note": note},
        headers={"Authorization": f"Bearer {token}"}
    )
    return r


def test_streak_calculation(token):
    print("\n=== Bug 1: Streak 计算测试 ===")
    
    r = requests.post(f"{BASE_URL}/api/habits/", json={
        "name": "测试streak习惯",
        "description": "用于测试streak计算",
        "category": "测试",
        "frequency_type": "daily",
        "frequency_count": 1
    }, headers={"Authorization": f"Bearer {token}"})
    habit_id = r.json()["id"]
    print(f"创建习惯: ID={habit_id}")
    
    today = date.today()
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)
    
    toggle_log(token, habit_id, two_days_ago, "前天打卡")
    print(f"前天({two_days_ago})打卡")
    
    r = requests.get(f"{BASE_URL}/api/habits/{habit_id}", 
        headers={"Authorization": f"Bearer {token}"})
    habit = r.json()
    streak_before = habit["current_streak"]
    print(f"前天打卡后 streak = {streak_before}")
    
    toggle_log(token, habit_id, yesterday, "昨天打卡")
    print(f"昨天({yesterday})打卡")
    
    r = requests.get(f"{BASE_URL}/api/habits/{habit_id}", 
        headers={"Authorization": f"Bearer {token}"})
    habit = r.json()
    streak_yesterday = habit["current_streak"]
    print(f"昨天打卡后 streak = {streak_yesterday}")
    
    toggle_log(token, habit_id, today, "今天打卡")
    print(f"今天({today})打卡")
    
    r = requests.get(f"{BASE_URL}/api/habits/{habit_id}", 
        headers={"Authorization": f"Bearer {token}"})
    habit = r.json()
    streak_today = habit["current_streak"]
    print(f"今天打卡后 streak = {streak_today}")
    
    toggle_log(token, habit_id, yesterday)
    print(f"取消昨天({yesterday})的打卡")
    
    r = requests.get(f"{BASE_URL}/api/habits/{habit_id}", 
        headers={"Authorization": f"Bearer {token}"})
    habit = r.json()
    streak_after_break = habit["current_streak"]
    print(f"取消昨天打卡后 streak = {streak_after_break}")
    
    if streak_after_break == 1:
        print("✅ Bug 1 修复验证通过：昨天没打卡，今天打卡后 streak 重置为 1")
    else:
        print(f"❌ Bug 1 修复验证失败：预期 streak=1，实际={streak_after_break}")
    
    requests.delete(f"{BASE_URL}/api/habits/{habit_id}", 
        headers={"Authorization": f"Bearer {token}"})
    
    return streak_after_break == 1


def test_challenge_progress(token):
    print("\n=== Bug 2: 挑战进度测试 ===")
    
    r = requests.post(f"{BASE_URL}/api/habits/", json={
        "name": "测试挑战习惯",
        "description": "用于测试挑战进度",
        "category": "测试",
        "frequency_type": "daily",
        "frequency_count": 1
    }, headers={"Authorization": f"Bearer {token}"})
    habit_id = r.json()["id"]
    print(f"创建习惯: ID={habit_id}")
    
    today = date.today()
    
    for i in range(1, 31):
        past_date = today - timedelta(days=i)
        toggle_log(token, habit_id, past_date, f"历史打卡 {i}")
    print("在挑战开始前，创建了30天历史打卡记录")
    
    challenge_start = today + timedelta(days=1)
    challenge_end = challenge_start + timedelta(days=29)
    
    r = requests.post(f"{BASE_URL}/api/challenges/", json={
        "habit_id": habit_id,
        "name": "测试挑战-验证开始日期过滤",
        "target_days": 30,
        "start_date": challenge_start.isoformat(),
        "end_date": challenge_end.isoformat()
    }, headers={"Authorization": f"Bearer {token}"})
    
    challenge_id = r.json()["id"]
    print(f"创建挑战: ID={challenge_id}, 开始日期={challenge_start}")
    
    r = requests.get(f"{BASE_URL}/api/challenges/{challenge_id}", 
        headers={"Authorization": f"Bearer {token}"})
    challenge = r.json()
    progress = challenge["current_progress"]
    print(f"挑战进度: {progress}/{challenge['target_days']}")
    
    if progress == 0:
        print("✅ Bug 2 修复验证通过：挑战开始前的历史记录没有被算入进度")
    else:
        print(f"❌ Bug 2 修复验证失败：预期进度=0，实际={progress}")
    
    requests.delete(f"{BASE_URL}/api/habits/{habit_id}", 
        headers={"Authorization": f"Bearer {token}"})
    
    return progress == 0


def test_cascade_delete(token):
    print("\n=== Bug 4: 级联删除测试 ===")
    
    r = requests.post(f"{BASE_URL}/api/habits/", json={
        "name": "测试级联删除习惯",
        "description": "用于测试级联删除",
        "category": "测试",
        "frequency_type": "daily",
        "frequency_count": 1
    }, headers={"Authorization": f"Bearer {token}"})
    habit_id = r.json()["id"]
    print(f"创建习惯: ID={habit_id}")
    
    today = date.today()
    for i in range(5):
        log_date = today - timedelta(days=i)
        toggle_log(token, habit_id, log_date, f"打卡记录 {i}")
    print("创建了5条打卡记录")
    
    r = requests.post(f"{BASE_URL}/api/challenges/", json={
        "habit_id": habit_id,
        "name": "级联删除测试挑战",
        "target_days": 30,
        "start_date": today.isoformat(),
        "end_date": (today + timedelta(days=29)).isoformat()
    }, headers={"Authorization": f"Bearer {token}"})
    challenge_id = r.json()["id"]
    print(f"创建挑战: ID={challenge_id}")
    
    r = requests.get(f"{BASE_URL}/api/habit-logs/recent-notes", 
        headers={"Authorization": f"Bearer {token}"})
    notes_before = r.json()
    habit_notes_before = [n for n in notes_before if n["habit_id"] == habit_id]
    print(f"删除前，该习惯的备注记录: {len(habit_notes_before)} 条")
    
    r = requests.get(f"{BASE_URL}/api/challenges/", 
        headers={"Authorization": f"Bearer {token}"})
    challenges_before = r.json()
    habit_challenges_before = [c for c in challenges_before if c["habit_id"] == habit_id]
    print(f"删除前，该习惯的挑战: {len(habit_challenges_before)} 个")
    
    r = requests.delete(f"{BASE_URL}/api/habits/{habit_id}", 
        headers={"Authorization": f"Bearer {token}"})
    print(f"删除习惯: {r.status_code}")
    
    r = requests.get(f"{BASE_URL}/api/habit-logs/recent-notes", 
        headers={"Authorization": f"Bearer {token}"})
    notes_after = r.json()
    habit_notes_after = [n for n in notes_after if n["habit_id"] == habit_id]
    print(f"删除后，该习惯的备注记录: {len(habit_notes_after)} 条")
    
    r = requests.get(f"{BASE_URL}/api/challenges/", 
        headers={"Authorization": f"Bearer {token}"})
    challenges_after = r.json()
    habit_challenges_after = [c for c in challenges_after if c["habit_id"] == habit_id]
    print(f"删除后，该习惯的挑战: {len(habit_challenges_after)} 个")
    
    if len(habit_notes_after) == 0 and len(habit_challenges_after) == 0:
        print("✅ Bug 4 修复验证通过：删除习惯后，相关打卡记录和挑战数据被级联删除")
    else:
        print(f"❌ Bug 4 修复验证失败：还有 {len(habit_notes_after)} 条日志、{len(habit_challenges_after)} 个挑战残留")
    
    return len(habit_notes_after) == 0 and len(habit_challenges_after) == 0


def main():
    print("=" * 60)
    print("Bug 修复验证测试")
    print("=" * 60)
    
    token = get_token()
    print("✅ 登录成功，获取 token")
    
    results = {}
    
    try:
        results["Bug 1: Streak 计算"] = test_streak_calculation(token)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Bug 1 测试出错: {e}")
        results["Bug 1: Streak 计算"] = False
    
    try:
        results["Bug 2: 挑战进度"] = test_challenge_progress(token)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Bug 2 测试出错: {e}")
        results["Bug 2: 挑战进度"] = False
    
    try:
        results["Bug 4: 级联删除"] = test_cascade_delete(token)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Bug 4 测试出错: {e}")
        results["Bug 4: 级联删除"] = False
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    for bug, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {bug}")
    
    print("\n📊 Bug 3 (饼图颜色和图例) 需要在浏览器中查看统计页面验证")
    print("=" * 60)


if __name__ == "__main__":
    main()
