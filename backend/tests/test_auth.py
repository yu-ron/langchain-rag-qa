"""
认证模块测试
测试注册、登录、获取信息、修改密码
"""
import pytest
import pytest_asyncio


class TestRegister:
    """用户注册测试"""

    async def test_register_success(self, client):
        """正常注册新用户"""
        response = await client.post("/api/auth/register", json={
            "username": "newuser", "password": "pass123456"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "注册成功"
        assert data["user"]["username"] == "newuser"
        assert data["user"]["role"] == "user"

    async def test_register_duplicate(self, client):
        """重复注册同名用户应失败"""
        await client.post("/api/auth/register", json={
            "username": "dupuser", "password": "pass123456"
        })
        response = await client.post("/api/auth/register", json={
            "username": "dupuser", "password": "pass123456"
        })
        assert response.status_code == 400
        assert "已被占用" in response.json()["detail"]

    async def test_register_short_username(self, client):
        """用户名太短应失败"""
        response = await client.post("/api/auth/register", json={
            "username": "ab", "password": "pass123456"
        })
        assert response.status_code == 422  # Pydantic 校验失败

    async def test_register_short_password(self, client):
        """密码太短应失败"""
        response = await client.post("/api/auth/register", json={
            "username": "validuser", "password": "12345"
        })
        assert response.status_code == 422


class TestLogin:
    """用户登录测试"""

    async def test_login_success(self, client, admin_token):
        """管理员登录成功"""
        assert admin_token is not None
        assert len(admin_token) > 20  # JWT Token 至少几十个字符

    async def test_login_wrong_password(self, client):
        """密码错误应拒绝"""
        response = await client.post("/api/auth/login", json={
            "username": "admin", "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    async def test_login_nonexistent_user(self, client):
        """不存在的用户应拒绝"""
        response = await client.post("/api/auth/login", json={
            "username": "nobody", "password": "123456"
        })
        assert response.status_code == 401


class TestUserInfo:
    """获取用户信息测试"""

    async def test_get_me_with_token(self, client, user_token):
        """带 Token 获取信息应成功"""
        response = await client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {user_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["role"] == "user"

    async def test_get_me_without_token(self, client):
        """不带 Token 应拒绝"""
        response = await client.get("/api/auth/me")
        assert response.status_code == 401

    async def test_get_me_with_bad_token(self, client):
        """伪造 Token 应拒绝"""
        response = await client.get("/api/auth/me", headers={
            "Authorization": "Bearer fake-token-12345"
        })
        assert response.status_code == 401


class TestChangePassword:
    """修改密码测试"""

    async def test_change_password_success(self, client, user_token):
        """正确修改密码"""
        response = await client.post("/api/auth/change-password", json={
            "old_password": "test123456",
            "new_password": "newpass123456"
        }, headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 200
        assert response.json()["message"] == "密码修改成功"

        # 用新密码登录应成功
        response = await client.post("/api/auth/login", json={
            "username": "testuser", "password": "newpass123456"
        })
        assert response.status_code == 200

        # 把密码改回去，避免影响其他测试
        new_token = response.json()["token"]
        await client.post("/api/auth/change-password", json={
            "old_password": "newpass123456",
            "new_password": "test123456"
        }, headers={"Authorization": f"Bearer {new_token}"})

    async def test_change_password_wrong_old(self, client, user_token):
        """旧密码错误应拒绝"""
        response = await client.post("/api/auth/change-password", json={
            "old_password": "wrongoldpassword",
            "new_password": "newpass123456"
        }, headers={"Authorization": f"Bearer {user_token}"})
        assert response.status_code == 400
        assert "旧密码错误" in response.json()["detail"]
