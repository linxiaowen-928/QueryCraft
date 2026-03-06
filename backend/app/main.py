"""
QueryCraft - 自然语言转SQL引擎
FastAPI 主应用
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.config import settings
from app.api import router


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
    
    # 注册路由
    app.include_router(router, prefix="/api/v1")
    
    @app.get("/", tags=["根"])
    async def root():
        """根路径"""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
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