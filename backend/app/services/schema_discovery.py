"""
Schema Discovery Service
自动发现数据库结构
"""
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ColumnInfo:
    """列信息"""
    name: str
    type: str
    comment: Optional[str] = None
    nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    default_value: Optional[str] = None


@dataclass
class TableInfo:
    """表信息"""
    name: str
    comment: Optional[str] = None
    columns: List[ColumnInfo] = field(default_factory=list)


@dataclass
class DatabaseInfo:
    """数据库信息"""
    name: str
    tables: List[TableInfo] = field(default_factory=list)


class SchemaDiscovery:
    """
    Schema 自动发现服务
    
    功能：
    1. 自动获取数据库完整结构
    2. 提取字段类型、注释、约束等元信息
    3. 支持增量更新
    """
    
    def __init__(self):
        self._schema_cache: Dict[str, DatabaseInfo] = {}
    
    async def discover_database(self, connector) -> DatabaseInfo:
        """
        发现数据库完整结构
        
        Args:
            connector: 数据库连接器实例
            
        Returns:
            DatabaseInfo: 数据库结构信息
        """
        logger.info("开始发现数据库结构...")
        
        database_name = await connector.get_database_name()
        
        # 获取所有表
        tables = await self.discover_tables(connector)
        
        database_info = DatabaseInfo(
            name=database_name,
            tables=tables
        )
        
        # 缓存结果
        self._schema_cache[database_name] = database_info
        
        logger.info(f"数据库结构发现完成: {len(tables)} 个表")
        return database_info
    
    async def discover_tables(self, connector) -> List[TableInfo]:
        """发现所有表"""
        tables = []
        
        # 获取表列表
        table_names = await connector.get_tables()
        
        for table_name in table_names:
            table_info = await self.discover_table(connector, table_name)
            tables.append(table_info)
        
        return tables
    
    async def discover_table(self, connector, table_name: str) -> TableInfo:
        """发现单个表的结构"""
        columns = await self.discover_columns(connector, table_name)
        
        # 尝试获取表注释
        table_comment = await connector.get_table_comment(table_name)
        
        return TableInfo(
            name=table_name,
            comment=table_comment,
            columns=columns
        )
    
    async def discover_columns(self, connector, table_name: str) -> List[ColumnInfo]:
        """发现表的列信息"""
        columns = []
        
        # 获取列信息
        column_data = await connector.get_columns(table_name)
        
        for col in column_data:
            column_info = ColumnInfo(
                name=col.get('name', ''),
                type=col.get('type', ''),
                comment=col.get('comment'),
                nullable=col.get('nullable', True),
                is_primary_key=col.get('is_primary_key', False),
                is_foreign_key=col.get('is_foreign_key', False),
                default_value=col.get('default')
            )
            columns.append(column_info)
        
        return columns
    
    def get_schema(self, database_name: str) -> Optional[DatabaseInfo]:
        """获取缓存的 Schema"""
        return self._schema_cache.get(database_name)
    
    def clear_cache(self, database_name: Optional[str] = None):
        """清除缓存"""
        if database_name:
            self._schema_cache.pop(database_name, None)
        else:
            self._schema_cache.clear()
    
    def to_dict(self, database_info: DatabaseInfo) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": database_info.name,
            "tables": [
                {
                    "name": table.name,
                    "comment": table.comment,
                    "columns": [
                        {
                            "name": col.name,
                            "type": col.type,
                            "comment": col.comment,
                            "nullable": col.nullable,
                            "is_primary_key": col.is_primary_key,
                            "is_foreign_key": col.is_foreign_key,
                            "default_value": col.default_value
                        }
                        for col in table.columns
                    ]
                }
                for table in database_info.tables
            ]
        }


# 全局实例
schema_discovery = SchemaDiscovery()
