"""
知识库管理模块测试
需要管理员权限
"""
import io
import pytest


class TestKnowledgeAuth:
    """知识库权限测试"""

    async def test_upload_as_user(self, client, user_token):
        """普通用户不能上传文档"""
        response = await client.post("/api/knowledge/upload",
            headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 403  # 禁止访问

    async def test_list_as_user(self, client, user_token):
        """普通用户不能查看文档列表"""
        response = await client.get("/api/knowledge/documents",
            headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 403

    async def test_stats_as_user(self, client, user_token):
        """普通用户不能查看知识库统计"""
        response = await client.get("/api/knowledge/stats",
            headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 403


class TestKnowledgeAdmin:
    """管理员知识库操作测试"""

    async def test_get_stats_empty(self, client, admin_token):
        """空知识库统计"""
        response = await client.get("/api/knowledge/stats",
            headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["document_count"] == 0
        assert data["completed"] == 0

    async def test_get_documents_empty(self, client, admin_token):
        """空文档列表"""
        response = await client.get("/api/knowledge/documents",
            headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    async def test_upload_text_file(self, client, admin_token):
        """上传文本文件"""
        text = "iPhone 15 supports 5G, A16 chip, 6.1 inch screen, 2-day battery."
        file_content = text.encode("utf-8")
        files = {"file": ("test_product.txt", io.BytesIO(file_content), "text/plain")}
        response = await client.post("/api/knowledge/upload",
            files=files,
            headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "上传成功"
        assert data["status"] == "completed"

    async def test_upload_invalid_type(self, client, admin_token):
        """上传不支持的文件类型应拒绝"""
        file_content = b"fake image content"
        files = {"file": ("photo.jpg", io.BytesIO(file_content), "image/jpeg")}
        response = await client.post("/api/knowledge/upload",
            files=files,
            headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 400
        assert "不支持" in response.json()["detail"]

    async def test_delete_nonexistent(self, client, admin_token):
        """删除不存在的文档"""
        response = await client.delete("/api/knowledge/documents/99999",
            headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 404
