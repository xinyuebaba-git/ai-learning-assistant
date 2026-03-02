"""
API 路由测试
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


class TestAuthAPI:
    """认证 API 测试"""

    def test_register_success(self, client, mock_db):
        """测试注册成功"""
        with patch("app.api.auth.get_db", return_value=mock_db):
            response = client.post(
                "/api/auth/register",
                json={
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": "password123"
                }
            )
            assert response.status_code == 201
            assert "username" in response.json()

    def test_register_duplicate_email(self, client, mock_db):
        """测试重复邮箱注册"""
        with patch("app.api.auth.get_db", return_value=mock_db):
            # 第一次注册
            response1 = client.post(
                "/api/auth/register",
                json={
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": "password123"
                }
            )
            
            # 第二次注册相同邮箱
            response2 = client.post(
                "/api/auth/register",
                json={
                    "email": "test@example.com",
                    "username": "anotheruser",
                    "password": "password123"
                }
            )
            assert response2.status_code == 400

    def test_login_success(self, client, mock_db):
        """测试登录成功"""
        with patch("app.api.auth.get_db", return_value=mock_db):
            response = client.post(
                "/api/auth/login",
                json={
                    "username": "testuser",
                    "password": "password123"
                }
            )
            assert response.status_code == 200
            assert "access_token" in response.json()

    def test_login_invalid_credentials(self, client, mock_db):
        """测试登录失败"""
        with patch("app.api.auth.get_db", return_value=mock_db):
            response = client.post(
                "/api/auth/login",
                json={
                    "username": "nonexistent",
                    "password": "wrongpassword"
                }
            )
            assert response.status_code == 401


class TestVideoAPI:
    """视频 API 测试"""

    def test_list_videos(self, client, mock_db):
        """测试获取视频列表"""
        with patch("app.api.videos.get_db", return_value=mock_db):
            response = client.get("/api/videos")
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    def test_list_videos_with_search(self, client, mock_db):
        """测试搜索视频"""
        with patch("app.api.videos.get_db", return_value=mock_db):
            response = client.get("/api/videos?search=test")
            assert response.status_code == 200

    def test_get_video_not_found(self, client, mock_db):
        """测试获取不存在的视频"""
        with patch("app.api.videos.get_db", return_value=mock_db):
            response = client.get("/api/videos/99999")
            assert response.status_code == 404


class TestSearchAPI:
    """搜索 API 测试"""

    def test_search_empty_query(self, client):
        """测试空查询"""
        response = client.get("/api/search?q=")
        assert response.status_code == 422  # 验证错误

    def test_search_with_query(self, client, mock_search_service):
        """测试有查询词的搜索"""
        with patch("app.api.search.get_search_service", return_value=mock_search_service):
            response = client.get("/api/search?q=测试")
            assert response.status_code == 200
            assert "results" in response.json()

    def test_search_suggestions(self, client, mock_search_service):
        """测试搜索建议"""
        with patch("app.api.search.get_search_service", return_value=mock_search_service):
            response = client.get("/api/search/suggestions?q=测试")
            assert response.status_code == 200
            assert "suggestions" in response.json()


class TestHealthCheck:
    """健康检查测试"""

    def test_root(self, client):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        assert "name" in response.json()
        assert response.json()["name"] == "Course AI Helper"

    def test_health(self, client):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


# Mock fixtures
@pytest.fixture
def mock_db():
    """Mock 数据库会话"""
    mock = AsyncMock()
    mock.execute = AsyncMock()
    mock.commit = AsyncMock()
    mock.refresh = AsyncMock()
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def mock_search_service():
    """Mock 搜索服务"""
    mock = Mock()
    mock.search = AsyncMock(return_value=[])
    mock.get_suggestions = AsyncMock(return_value=[])
    return mock
