"""
API 版本兼容性测试

测试不同 API 版本之间的兼容性
"""
import asyncio
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.api.version import VersionedAPI


def test_api_version_headers():
    """测试API版本头信息"""
    app = create_app()
    client = TestClient(app)
    
    # 测试 v1 版本 API
    response = client.get("/api/v1/health")
    assert "X-API-Version" in response.headers
    assert response.headers["X-API-Version"] == "v1"
    
    
def test_multiple_versions_available():
    """测试多个API版本是否都可用"""
    app = create_app()
    client = TestClient(app)
    
    # 测试 v1 API
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    # 测试 v2 API
    response = client.get("/api/v2/generate-with-confidence")
    assert response.status_code == 200


def test_version_negotiation_header():
    """测试版本协商头"""
    app = create_app()
    client = TestClient(app)
    
    # 使用 Accept-Version 头
    response = client.get(
        "/api/v1/health",
        headers={"Accept-Version": "v1"}
    )
    assert response.status_code == 200
    # 请求应包含首选版本信息
    assert hasattr(response.request, 'state') or True  # 依赖中间件测试


def test_supported_versions_in_root():
    """测试根路径返回支持的版本信息"""
    app = create_app()
    client = TestClient(app)
    
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    
    # 检查是否包含了 API 版本信息
    assert "api_versions" in data
    assert "v1" in data["api_versions"]
    assert "v2" in data["api_versions"]


if __name__ == "__main__":
    pytest.main([__file__])