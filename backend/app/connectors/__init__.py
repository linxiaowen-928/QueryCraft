"""
数据源连接器
"""

from .base import BaseConnector, ConnectionConfig, QueryResult
from .mysql import MySQLConnector
from .postgresql import PostgreSQLConnector
from .manager import ConnectorManager, create_connector, manager

__all__ = [
    "BaseConnector",
    "ConnectionConfig",
    "QueryResult",
    "MySQLConnector",
    "PostgreSQLConnector",
    "ConnectorManager",
    "create_connector",
    "manager"
]