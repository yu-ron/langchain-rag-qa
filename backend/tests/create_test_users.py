"""
预创建 100 个测试账号
压测前运行一次：python tests/create_test_users.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests

BASE = "http://localhost:8000"

created = 0
for i in range(1, 101):
    username = f"loadtest_{i}"
    resp = requests.post(f"{BASE}/api/auth/register", json={
        "username": username,
        "password": "test123456",
    })
    if resp.status_code == 200:
        created += 1
        print(f"[{created:3d}/100] {username} 创建成功")
    else:
        print(f"[{created:3d}/100] {username} 已存在或失败: {resp.json().get('detail', '')}")

print(f"\n完成！共创建 {created} 个新账号（已有账号会跳过）")
