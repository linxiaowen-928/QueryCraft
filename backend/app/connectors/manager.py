"""
数据源连接器管理
"""

from typing import Dict, Optional
from .base import BaseConnector, ConnectionConfig
from .mysql import MySQLConnector
from .postgresql import PostgreSQLConnector


class ConnectorManager:
    """连接器管理器"""
    
    def __init__(self):
        self.connectors: Dict[str, BaseConnector] = {}
    
    def register(self, name: str, connector: BaseConnector):
        """注册连接器"""
        self.connectors[name] = connector
    
    def get(self, name: str) -> Optional[BaseConnector]:
        """获取连接器"""
        return self.connectors.get(name)
    
    async def connect(self, name: str) -> bool:
        """连接数据源"""
        connector = self.get(name)
        if connector:
            return await connector.connect()
        return False
    
    async def connect_all(self):
        """连接所有数据源"""
        for name, connector in self.connectors.items():
            try:
                await connector.connect()
            except Exception as e:
                print(f"Failed to connect {name}: {e}")
    
    async def close_all(self):
        """关闭所有连接"""
        for connector in self.connectors.values():
            await connector.close()
    
    def list_datasources(self) -> Dict[str, str]:
        """列出所有数据源"""
        return {name: conn.dialect for name, conn in self.connectors.items()}


def create_connector(config: ConnectionConfig, connector_type: str) -> BaseConnector:
    """创建连接器"""
    connectors = {
        "mysql": MySQLConnector,
        "postgresql": PostgreSQLConnector,
        # "hive": HiveConnector,
    }
    
    connector_class = connectors.get(connector_type)
    if not connector_class:
        raise ValueError(f"Unsupported connector type: {connector_type}")
    
    return connector_class(config)


# 全局管理器
manager = ConnectorManager()