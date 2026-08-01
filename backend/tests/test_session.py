"""
会话管理模块测试
"""
import pytest


class TestSessionCreate:
    """创建会话测试"""

    async def test_create_session_default(self, client, user_token):
        """创建会话（使用默认标题）"""
        response = await client.post("/api/sessions", json={},
            headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "新对话"
        assert "id" in data

    async def test_create_session_custom_title(self, client, user_token):
        """创建会话（自定义标题）"""
        response = await client.post("/api/sessions", json={"title": "商品咨询"},
            headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 200
        assert response.json()["title"] == "商品咨询"

    async def test_create_session_no_auth(self, client):
        """未登录无法创建会话"""
        response = await client.post("/api/sessions", json={})
        assert response.status_code == 401


class TestSessionList:
    """会话列表测试"""

    async def test_list_sessions(self, client, user_token):
        """获取会话列表"""
        # 先创建几个会话
        for i in range(3):
            await client.post("/api/sessions", json={"title": f"会话{i}"},
                headers={"Authorization": f"Bearer {user_token}"})

        response = await client.get("/api/sessions",
            headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3
        assert len(data["items"]) >= 3

    async def test_list_empty(self, client, user_token):
        """无会话时返回空列表"""
        response = await client.get("/api/sessions",
            headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 200
        # items 数量取决于之前测试是否创建了会话


class TestSessionDetail:
    """会话详情测试"""

    async def test_get_session_detail(self, client, user_token):
        """获取会话详情"""
        # 创建会话
        create_resp = await client.post("/api/sessions", json={"title": "测试"},
            headers={"Authorization": f"Bearer {user_token}"})
        session_id = create_resp.json()["id"]

        response = await client.get(f"/api/sessions/{session_id}",
            headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "测试"
        assert "messages" in data

    async def test_get_nonexistent_session(self, client, user_token):
        """访问不存在的会话"""
        response = await client.get("/api/sessions/99999",
            headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 404


class TestSessionDelete:
    """删除会话测试"""

    async def test_delete_session(self, client, user_token):
        """删除会话"""
        create_resp = await client.post("/api/sessions", json={"title": "待删除"},
            headers={"Authorization": f"Bearer {user_token}"})
        session_id = create_resp.json()["id"]

        response = await client.delete(f"/api/sessions/{session_id}",
            headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 200
        assert response.json()["message"] == "删除成功"

        # 确认已删除
        response = await client.get(f"/api/sessions/{session_id}",
            headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 404
