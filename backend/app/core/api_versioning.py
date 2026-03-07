"""
API 版本控制中间件和管理器

处理 API 版本控制、兼容性保证和版本文档等功能
"""
import re
from typing import Optional, Dict, Callable, Any
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.routing import APIRoute
import logging

logger = logging.getLogger(__name__)

class APIVersionManager:
    """
    API 版本管理器
    
    提供版本控制、兼容性保证和版本文档等功能
    """
    
    def __init__(self):
        self.supported_versions = set()
        self.deprecated_versions = {}
        self.compatibility_handlers = {}
        self.version_routes = {}
        
    def register_version(self, version: str, deprecated: bool = False, 
                        migration_guide: str = ""):
        """注册支持的API版本"""
        self.supported_versions.add(version)
        if deprecated:
            self.deprecated_versions[version] = migration_guide
        
    def is_supported(self, version: str) -> bool:
        """检查版本是否被支持"""
        return version in self.supported_versions
        
    def is_deprecated(self, version: str) -> bool:
        """检查版本是否已弃用"""
        return version in self.deprecated_versions
        
    def get_latest_version(self) -> str:
        """获取最新的API版本"""
        if not self.supported_versions:
            return "v1"
        
        # Sort versions by numerical order (v1, v2, v3, etc.)
        sorted_versions = sorted(self.supported_versions, 
                               key=lambda x: int(x[1:]) if x.startswith("v") and x[1:].isdigit() else 0)
        return sorted_versions[-1] if sorted_versions else "v1"
        
    def negotiate_version(self, request: Request) -> str:
        """通过请求头协商API版本"""
        # 首先尝试从Header中获取
        version_header = request.headers.get("X-API-Version")
        if version_header:
            if self.is_supported(version_header):
                return version_header
            else:
                # 返回兼容的版本或最新版本
                return self.get_latest_version()
        
        # 从 Accept header 解析 (例如: application/vnd.api.v2+json)
        accept_header = request.headers.get("Accept", "")
        version_match = re.search(r'vnd\.api\.v(\d+)\+json', accept_header)
        if version_match:
            api_version = f"v{version_match.group(1)}"
            if self.is_supported(api_version):
                return api_version
            else:
                return self.get_latest_version()
                
        # 然后尝试从 URL 路径解析
        path_parts = request.url.path.split("/")
        if len(path_parts) > 1:
            for part in path_parts[1:]:
                if part.startswith("v") and part[1:].isdigit():
                    if self.is_supported(part):
                        return part
                    else:
                        return self.get_latest_version()
        
        # 默认返回最新版本
        return self.get_latest_version()


class VersionMiddleware:
    """API 版本中间件"""
    
    def __init__(self, app, version_manager: APIVersionManager):
        self.app = app
        self.version_manager = version_manager
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope)
        version = self.version_manager.negotiate_version(request)
        
        # 添加版本信息到请求状态
        scope['api_version'] = version
        
        # 添加警告头如果使用弃用版本
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                if self.version_manager.is_deprecated(version):
                    message.setdefault("headers", []).append(
                        [b"X-API-Version-Warning", 
                         f"API 版本 {version} 已弃用，请参考迁移指南".encode()]
                    )
                    
                # 添加 API 版本信息到响应头
                message.setdefault("headers", []).append(
                    [b"X-API-Version", version.encode()]
                )
                
            await send(message)
        
        async def versioned_receive():
            # Add custom header for version to the request scope context
            if 'api_version' in scope:
                request.state.api_version = scope['api_version']
            return await receive()
        
        await self.app(scope, versioned_receive, send_wrapper)


# Global instance of the version manager
version_manager = APIVersionManager()


def setup_api_versioning(app: FastAPI) -> APIVersionManager:
    """
    为 FastAPI 应用设置 API 版本管理
    
    Args:
        app: FastAPI 应用实例
    
    Returns:
        APIVersionManager: 版本管理器实例
    """
    # Register the supported versions
    version_manager.register_version("v1", deprecated=False)
    version_manager.register_version("v2", deprecated=False)
    version_manager.register_version("v3", deprecated=False)
    
    # Add middleware to handle version negotiation
    app.add_middleware(VersionMiddleware, version_manager=version_manager)
    
    # Add root endpoint to expose API versions info
    @app.get("/versions", tags=["系统"], 
            summary="获取 API 版本信息",
            description="返回所有受支持的 API 版本信息")
    async def get_api_versions():
        """获取所有可用的 API 版本信息"""
        versions_info = []
        for version in version_manager.supported_versions:
            version_info = {
                "version": version,
                "status": "deprecated" if version_manager.is_deprecated(version) else "active",
                "latest": version_manager.get_latest_version() == version,
                "documentation_path": f"/api/{version}/docs",
            }
            if version in version_manager.deprecated_versions:
                version_info["migration_guide"] = version_manager.deprecated_versions[version]
            versions_info.append(version_info)
        
        return {
            "versions": sorted(versions_info, key=lambda x: int(x["version"][1:])),
            "latest_version": version_manager.get_latest_version(),
            "recommended_version": version_manager.get_latest_version(),
        }
    
    # Update root endpoint to show version info
    for route in app.routes:
        if hasattr(route, 'path') and route.path == "/":
            # Temporarily store old root handler
            old_endpoint = route.endpoint
            
            # Define new handler that calls old endpoint and adds version info
            async def enhanced_root():
                result = await old_endpoint()
                result["supported_versions"] = list(version_manager.supported_versions)
                result["latest_version"] = version_manager.get_latest_version()
                result["api_versions_endpoint"] = "/versions"
                return result
            route.endpoint = enhanced_root
            break
    
    return version_manager