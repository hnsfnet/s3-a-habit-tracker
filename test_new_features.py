import requests
import json

BASE_URL = "http://localhost:8000"

def login_and_get_token():
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": "testuser", "password": "123456"}
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    return None

def test_apis():
    token = login_and_get_token()
    if not token:
        print("❌ 登录失败")
        return
    
    print(f"✅ 登录成功，获取 token")
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n=== 测试打卡备注 API ===")
    
    today = "2025-10-21"
    
    print("\n1. 测试打卡并添加备注:")
    note = "今天跑了5公里，状态很好！"
    r = requests.post(
        f"{BASE_URL}/api/habit-logs/toggle/1",
        params={"log_date": today, "note": note},
        headers=headers
    )
    print(f"   POST /api/habit-logs/toggle/1: {r.status_code} - {r.json()}")
    
    print("\n2. 测试获取某天带备注的打卡记录:")
    r = requests.get(
        f"{BASE_URL}/api/habit-logs/date/{today}/with-notes",
        headers=headers
    )
    print(f"   GET /api/habit-logs/date/{today}/with-notes: {r.status_code}")
    print(f"   结果: {json.dumps(r.json(), ensure_ascii=False, indent=6)}")
    
    print("\n3. 测试更新备注:")
    new_note = "今天读了《Python编程》第3章，做了笔记"
    r = requests.put(
        f"{BASE_URL}/api/habit-logs/note/1/{today}",
        json={"note": new_note},
        headers=headers
    )
    print(f"   PUT /api/habit-logs/note/1/{today}: {r.status_code} - {r.json()}")
    
    print("\n4. 测试获取最近备注记录:")
    r = requests.get(
        f"{BASE_URL}/api/habit-logs/recent-notes?days=30",
        headers=headers
    )
    print(f"   GET /api/habit-logs/recent-notes: {r.status_code}")
    data = r.json()
    if isinstance(data, list):
        print(f"   返回 {len(data)} 条记录")
        for item in data[:3]:
            if item.get('note'):
                print(f"     - {item['date']}: {item['note'][:30]}...")
    else:
        print(f"   错误: {data}")
    
    print("\n=== 测试挑战 API ===")
    
    print("\n5. 测试创建挑战:")
    challenge_data = {
        "name": "连续30天阅读",
        "habit_id": 1,
        "target_days": 30,
        "start_date": today
    }
    r = requests.post(
        f"{BASE_URL}/api/challenges/",
        json=challenge_data,
        headers=headers
    )
    print(f"   POST /api/challenges/: {r.status_code}")
    if r.status_code == 200:
        challenge = r.json()
        print(f"   创建成功: ID={challenge['id']}, 名称={challenge['name']}")
        challenge_id = challenge['id']
    else:
        print(f"   错误: {r.text}")
        challenge_id = None
    
    print("\n6. 测试获取挑战列表:")
    r = requests.get(
        f"{BASE_URL}/api/challenges/",
        headers=headers
    )
    data = r.json()
    print(f"   GET /api/challenges/: {r.status_code}, 返回 {len(data)} 个挑战")
    for c in data[:2]:
        print(f"     - {c['name']}: 进度 {c['current_progress']}/{c['target_days']} ({c['progress_percent']}%)")
    
    if challenge_id:
        print(f"\n7. 测试获取单个挑战详情 (ID={challenge_id}):")
        r = requests.get(
            f"{BASE_URL}/api/challenges/{challenge_id}",
            headers=headers
        )
        print(f"   GET /api/challenges/{challenge_id}: {r.status_code}")
        c = r.json()
        print(f"     名称: {c['name']}")
        print(f"     进度: {c['current_progress']}/{c['target_days']}")
        print(f"     剩余: {c['remaining_days']} 天")
        print(f"     连续: {c['current_streak']} 天")
    
    print("\n=== 测试统计 API ===")
    
    print("\n8. 测试获取总体统计:")
    r = requests.get(
        f"{BASE_URL}/api/stats/overall",
        headers=headers
    )
    print(f"   GET /api/stats/overall: {r.status_code}")
    print(f"   {json.dumps(r.json(), ensure_ascii=False, indent=6)}")
    
    print("\n9. 测试获取30天趋势:")
    r = requests.get(
        f"{BASE_URL}/api/stats/30day-trend",
        headers=headers
    )
    data = r.json()
    print(f"   GET /api/stats/30day-trend: {r.status_code}, 返回 {len(data)} 天数据")
    for d in data[-5:]:
        print(f"     {d['date']}: {d['count']} 次")
    
    print("\n10. 测试获取分类占比:")
    r = requests.get(
        f"{BASE_URL}/api/stats/category-breakdown",
        headers=headers
    )
    data = r.json()
    print(f"   GET /api/stats/category-breakdown: {r.status_code}")
    for d in data:
        print(f"     {d['category']}: {d['count']} 次 ({d['percentage']}%)")
    
    print("\n11. 测试获取月度完成率:")
    r = requests.get(
        f"{BASE_URL}/api/stats/monthly-rates",
        headers=headers
    )
    data = r.json()
    print(f"   GET /api/stats/monthly-rates: {r.status_code}")
    for d in data:
        print(f"     {d['month']}: {d['rate']}%")
    
    print("\n12. 测试获取单个习惯月度完成率:")
    r = requests.get(
        f"{BASE_URL}/api/stats/monthly-rates?habit_id=1",
        headers=headers
    )
    data = r.json()
    print(f"   GET /api/stats/monthly-rates?habit_id=1: {r.status_code}")
    for d in data:
        print(f"     {d['month']}: {d['rate']}%")
    
    print("\n" + "="*50)
    print("✅ 所有 API 测试完成！")
    print("="*50)

if __name__ == "__main__":
    test_apis()
