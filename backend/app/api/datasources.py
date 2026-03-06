"""
数据源管理 API
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from app.connectors import manager, ConnectionConfig, create_connector

router = APIRouter(prefix="/datasources", tags=["数据源"])


class DataSourceCreate(BaseModel):
    """创建数据源请求"""
    name: str
    type: str  # mysql, postgresql, hive, etc.
    host: str
    port: int
    database: str
    username: Optional[str] = None
    password: Optional[str] = None
    properties: Optional[Dict[str, str]] = None


class DataSourceInfo(BaseModel):
    """数据源信息"""
    name: str
    type: str
    host: str
    port: int
    database: str
    connected: bool


@router.get("/", response_model=List[DataSourceInfo])
async def list_datasources():
    """列出所有数据源"""
    result = []
    for name, conn in manager.connectors.items():
        result.append(DataSourceInfo(
            name=name,
            type=conn.dialect,
            host=conn.config.host,
            port=conn.config.port,
            database=conn.config.database,
            connected=conn.connected
        ))
    return result


@router.post("/")
async def create_datasource(ds: DataSourceCreate):
    """创建并连接数据源"""
    try:
        config = ConnectionConfig(
            host=ds.host,
            port=ds.port,
            database=ds.database,
            username=ds.username,
            password=ds.password,
            properties=ds.properties
        )
        
        connector = create_connector(config, ds.type)
        await connector.connect()
        
        manager.register(ds.name, connector)
        
        return {"success": True, "message": f"数据源 '{ds.name}' 已创建并连接"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{name}/schema")
async def get_schema(name: str):
    """获取数据源Schema"""
    connector = manager.get(name)
    if not connector:
        raise HTTPException(status_code=404, detail=f"数据源 '{name}' 不存在")
    
    if not connector.connected:
        raise HTTPException(status_code=400, detail="数据源未连接")
    
    try:
        schema = await connector.get_schema()
        return schema
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{name}/execute")
async def execute_sql(name: str, sql: str, limit: int = 1000):
    """执行SQL"""
    connector = manager.get(name)
    if not connector:
        raise HTTPException(status_code=404, detail=f"数据源 '{name}' 不存在")
    
    if not connector.connected:
        raise HTTPException(status_code=400, detail="数据源未连接")
    
    try:
        result = await connector.execute(sql, limit)
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{name}")
async def delete_datasource(name: str):
    """删除数据源"""
    connector = manager.get(name)
    if not connector:
        raise HTTPException(status_code=404, detail=f"数据源 '{name}' 不存在")
    
    await connector.close()
    del manager.connectors[name]
    
    return {"success": True, "message": f"数据源 '{name}' 已删除"}