"""
PostgreSQL 连接器
"""

import asyncpg
from typing import Dict, Any, List, Optional
import time

from .base import BaseConnector, ConnectionConfig, QueryResult


class PostgreSQLConnector(BaseConnector):
    """PostgreSQL 数据源连接器"""
    
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.pool: Optional[asyncpg.Pool] = None
    
    @property
    def dialect(self) -> str:
        return "postgresql"
    
    async def connect(self) -> bool:
        """建立连接池"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                user=self.config.username,
                password=self.config.password,
                database=self.config.database,
                min_size=1,
                max_size=10
            )
            self.connected = True
            return True
        except Exception as e:
            self.connected = False
            raise ConnectionError(f"PostgreSQL connection failed: {e}")
    
    async def test_connection(self) -> bool:
        """测试连接"""
        if not self.pool:
            return False
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
                return True
        except:
            return False
    
    async def get_schema(self) -> Dict[str, Any]:
        """获取数据库Schema"""
        if not self.pool:
            raise RuntimeError("Not connected")
        
        schema = {
            "database": self.config.database,
            "tables": []
        }
        
        async with self.pool.acquire() as conn:
            # 获取表列表
            tables = await conn.fetch("""
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            
            for table in tables:
                table_name = table["table_name"]
                table_info = {
                    "name": table_name,
                    "columns": []
                }
                
                # 获取列信息
                columns = await conn.fetch("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = $1
                    ORDER BY ordinal_position
                """, table_name)
                
                for col in columns:
                    table_info["columns"].append({
                        "name": col["column_name"],
                        "type": col["data_type"],
                        "nullable": col["is_nullable"] == "YES",
                        "default": col["column_default"]
                    })
                
                schema["tables"].append(table_info)
        
        return schema
    
    async def execute(self, sql: str, limit: int = 1000) -> QueryResult:
        """执行SQL查询"""
        if not self.pool:
            raise RuntimeError("Not connected")
        
        start_time = time.time()
        
        try:
            async with self.pool.acquire() as conn:
                # 添加 LIMIT
                if limit > 0 and "LIMIT" not in sql.upper():
                    sql = f"{sql} LIMIT {limit}"
                
                # 执行查询
                rows = await conn.fetch(sql)
                
                # 获取列名
                if rows:
                    columns = list(rows[0].keys())
                else:
                    columns = []
                
                # 转换为字典列表
                rows_list = [dict(row) for row in rows]
                
                return QueryResult(
                    success=True,
                    columns=columns,
                    rows=rows_list,
                    total_rows=len(rows_list),
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )
                
        except Exception as e:
            return QueryResult(
                success=False,
                error=str(e),
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
    
    async def close(self):
        """关闭连接池"""
        if self.pool:
            await self.pool.close()
            self.pool = None
        self.connected = False