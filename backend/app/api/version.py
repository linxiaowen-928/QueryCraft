"""
API 版本管理模块

支持多版本 API 管理，提供版本协商、向后兼容等功能
"""
from enum import Enum
from typing import Optional, Dict, Any
from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import JSONResponse
from app.config import settings


class ApiVersion(str, Enum):
    """API版本枚举"""
    V1 = "v1"
    V2 = "v2"


def determine_api_version_from_path(path: str) -> Optional[str]:
    """从路径确定 API 版本"""
    if path.startswith("/api/v1"):
        return "v1"
    elif path.startswith("/api/v2"):
        return "v2"
    return None


class VersionedAPI:
    """版本化API管理类"""
    
    def __init__(self):
        self.versions: Dict[str, APIRouter] = {}
        self.deprecated_versions: set = set()
        self.compatibility_map: Dict[str, str] = {}  # v2 -> v1 映射表
    
    def register_version(self, version: ApiVersion, router: APIRouter, deprecated: bool = False):
        """注册版本路由"""
        self.versions[version.value] = router
        
        if deprecated:
            self.deprecated_versions.add(version.value)
    
    def is_deprecated(self, version: str) -> bool:
        """判断版本是否已弃用"""
        return version in self.deprecated_versions
    
    def get_supported_versions(self) -> list:
        """获取支持的版本列表"""
        return list(self.versions.keys())
    
    def create_versioned_app(self, app: FastAPI) -> FastAPI:
        """为应用创建版本化路由"""
        
        # 为每个版本注册路由
        for version_value, router in self.versions.items():
            prefix = f"/api/{version_value}"
            app.include_router(router, prefix=prefix)
            
            # 如果版本已弃用，添加警告头
            if self.is_deprecated(version_value):
                self._add_deprecation_middleware(app, prefix)
        
        return app
    
    def _add_deprecation_middleware(self, app: FastAPI, prefix: str):
        """为废弃版本添加中间件"""
        @app.middleware("http")
        async def deprecation_warning_middleware(request: Request, call_next):
            if request.url.path.startswith(prefix):
                response = await call_next(request)
                
                # 添加弃用警告头
                if isinstance(response, JSONResponse):
                    response.headers["X-API-Version-Deprecated"] = "true"
                    response.headers["X-API-Migration-Guide"] = "/docs/migration-guide"
                    
                return response
            
            return await call_next(request)


def create_version_negotiation_middleware(app: FastAPI):
    """创建版本协商中间件（通过请求头决定版本）"""
    @app.middleware("http")
    async def version_negotiation_middleware(request: Request, call_next):
        # 如果客户端通过 Accept-Version 请求头指定了首选版本
        accept_version = request.headers.get("Accept-Version")
        if accept_version:
            # 设置请求状态中的首选版本
            request.state.preferred_version = accept_version
        
        response = await call_next(request)
        
        # 添加当前 API 版本信息到响应头部
        current_version = determine_api_version_from_path(request.url.path)
        if current_version:
            response.headers["X-API-Version"] = current_version
        
        return response
    
    return app