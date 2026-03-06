"""API package"""
from fastapi import APIRouter
from .routes import router as main_router
from .datasources import router as ds_router

# 合并路由
router = APIRouter()
router.include_router(main_router)
router.include_router(ds_router, prefix="/datasources", tags=["数据源"])

__all__ = ["router"]