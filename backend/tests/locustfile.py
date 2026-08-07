"""
LangChain RAG 系统 — 压力测试脚本

使用方式：
  1. 先初始化测试账号：python tests/create_test_users.py
  2. 启动后端（Mock 模式）：MOCK_LLM=true python main.py
  3. 启动压测：locust -f tests/locustfile.py --host=http://localhost:8000
  4. 打开 http://localhost:8089 设置用户数，开始测试
"""
import time
import random
from locust import HttpUser, task, between


# 预创建的测试账号前缀（运行 create_test_users.py 生成）
TEST_USER_PREFIX = "loadtest_"


class RAGUser(HttpUser):
    """
    模拟普通用户：从预创建账号池中随机取一个登录，然后进行问答
    不包含注册（由 create_test_users.py 预先创建），避免 bcrypt 成为瓶颈
    """

    weight = 95
    wait_time = between(1, 3)

    def on_start(self):
        """随机取一个预创建的测试账号登录"""
        user_num = random.randint(1, 100)
        self.username = f"{TEST_USER_PREFIX}{user_num}"
        self.password = "test123456"

        resp = self.client.post("/api/auth/login", json={
            "username": self.username,
            "password": self.password,
        })
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("token", "")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = ""
            self.headers = {}

        # 创建会话
        if self.token:
            resp = self.client.post("/api/sessions",
                json={"title": f"压测-{user_num}"},
                headers=self.headers,
                name="/api/sessions (创建)")
            if resp.status_code == 200:
                self.session_id = resp.json().get("id", 1)
            else:
                self.session_id = 1
        else:
            self.session_id = 1

    @task(5)
    def ask_question(self):
        """核心：向知识库提问"""
        if not self.token:
            return
        self.client.post(
            "/api/chat/ask",
            json={
                "session_id": self.session_id,
                "question": f"请介绍一下这款商品的特点和参数？",
            },
            headers=self.headers,
            name="/api/chat/ask",
        )

    @task(3)
    def list_sessions(self):
        """查看会话列表"""
        if not self.token:
            return
        self.client.get(
            "/api/sessions",
            headers=self.headers,
            name="/api/sessions (列表)",
        )

    @task(2)
    def get_me(self):
        """查看个人信息"""
        if not self.token:
            return
        self.client.get(
            "/api/auth/me",
            headers=self.headers,
            name="/api/auth/me",
        )


class AdminUser(HttpUser):
    """管理员：查看知识库统计和文档列表"""

    weight = 5
    wait_time = between(2, 5)

    def on_start(self):
        resp = self.client.post("/api/auth/login", json={
            "username": "admin",
            "password": "123456",
        })
        if resp.status_code == 200:
            self.token = resp.json().get("token", "")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = ""
            self.headers = {}

    @task
    def view_stats(self):
        if not self.token:
            return
        self.client.get(
            "/api/knowledge/stats",
            headers=self.headers,
            name="/api/knowledge/stats",
        )

    @task
    def list_documents(self):
        if not self.token:
            return
        self.client.get(
            "/api/knowledge/documents",
            headers=self.headers,
            name="/api/knowledge/documents",
        )
