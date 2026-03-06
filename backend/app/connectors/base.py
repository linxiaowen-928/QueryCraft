"""
数据源连接器
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ConnectionConfig(BaseModel):
    """连接配置"""
    host: str
    port: int
    database: str
    username: Optional[str] = None
    password: Optional[str] = None
    properties: Optional[Dict[str, str]] = None


class QueryResult(BaseModel):
    """查询结果"""
    success: bool
    columns: List[str] = []
    rows: List[Dict[str, Any]] = []
    total_rows: int = 0
    error: Optional[str] = None
    execution_time_ms: int = 0


class BaseConnector(ABC):
    """连接器基类"""
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """建立连接"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """测试连接"""
        pass
    
    @abstractmethod
    async def get_schema(self) -> Dict[str, Any]:
        """获取Schema"""
        pass
    
    @abstractmethod
    async def execute(self, sql: str, limit: int = 1000) -> QueryResult:
        """执行SQL"""
        pass
    
    @abstractmethod
    async def close(self):
        """关闭连接"""
        pass
    
    @property
    @abstractmethod
    def dialect(self) -> str:
        """SQL方言"""
        pass