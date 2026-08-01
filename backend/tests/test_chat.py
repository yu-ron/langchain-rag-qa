"""
聊天模块测试
"""
import pytest


class TestChat:
    """聊天测试"""

    async def test_chat_without_auth(self, client):
        """未登录不能提问"""
        response = await client.post("/api/chat/ask", json={
            "session_id": 1, "question": "测试问题"
        })
        assert response.status_code == 401

    async def test_chat_empty_question(self, client, user_token):
        """空问题应被拒绝"""
        response = await client.post("/api/chat/ask", json={
            "session_id": 1, "question": ""
        }, headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 422  # Pydantic 校验

    async def test_chat_question_too_long(self, client, user_token):
        """超长问题应拒绝"""
        response = await client.post("/api/chat/ask", json={
            "session_id": 1, "question": "x" * 2001
        }, headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 422

    async def test_feedback_invalid(self, client, user_token):
        """无效反馈值应拒绝"""
        response = await client.post("/api/chat/feedback", json={
            "message_id": 1, "feedback": "bad"
        }, headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 422


class TestExport:
    """对话导出测试"""

    async def test_export_no_auth(self, client):
        """未登录不能导出"""
        response = await client.get("/api/export/session/1")
        assert response.status_code == 401

    async def test_export_nonexistent(self, client, user_token):
        """导出不存在的会话"""
        response = await client.get("/api/export/session/99999",
            headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 404
