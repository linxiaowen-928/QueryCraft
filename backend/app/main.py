"""
QueryCraft - 自然语言转SQL引擎
FastAPI 主应用
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.config import settings
from app.api import router
from app.api import versioned_routes
from app.api.version import ApiVersion, VersionedAPI, create_version_negotiation_middleware

def create_app() -> FastAPI:
    """创建FastAPI应用"""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="工业化级别的自然语言到SQL转换引擎",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    # 设置API版本管理
    from app.api.v2_routes import v2_router
    from app.api.versioned_routes import setup_versioned_routes
    # 注册版本化的API路由
    version_manager = VersionedAPI()
    
    # 设置当前 v1 版本路由器（包含所有现有API）
    version_manager.register_version(ApiVersion.V1, v1_router, prefix='/api/v1')
    # 注册v2版本，包含更多功能和更好的置信度评估机制
    version_manager.register_version(ApiVersion.V2, v2_router, prefix='/api/v2')
    # 创建版本化应用程序
    version_manager.create_versioned_app(app)

    # 添加版本协商中间件以根据请求头等确定应使用哪个版本
    app.middleware('http')(create_version_negotiation_middleware)

    @app.get("/", tags=["根"])
    async def root():
        """根路径，添加支持的版本信息"""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "api_versions": [ApiVersion.V1.value, ApiVersion.V2.value],  # 支持的API版本
            "timestamp": datetime.utcnow().isoformat()
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )