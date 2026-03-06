"""
MySQL 连接器
"""

import aiomysql
from typing import Dict, Any, List, Optional
import time

from .base import BaseConnector, ConnectionConfig, QueryResult


class MySQLConnector(BaseConnector):
    """MySQL 数据源连接器"""
    
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.pool: Optional[aiomysql.Pool] = None
    
    @property
    def dialect(self) -> str:
        return "mysql"
    
    async def connect(self) -> bool:
        """建立连接池"""
        try:
            self.pool = await aiomysql.create_pool(
                host=self.config.host,
                port=self.config.port,
                user=self.config.username,
                password=self.config.password,
                db=self.config.database,
                minsize=1,
                maxsize=10,
                autocommit=True
            )
            self.connected = True
            return True
        except Exception as e:
            self.connected = False
            raise ConnectionError(f"MySQL connection failed: {e}")
    
    async def test_connection(self) -> bool:
        """测试连接"""
        if not self.pool:
            return False
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1")
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
            async with conn.cursor() as cur:
                # 获取表列表
                await cur.execute("SHOW TABLES")
                tables = await cur.fetchall()
                
                for (table_name,) in tables:
                    table_info = {
                        "name": table_name,
                        "columns": []
                    }
                    
                    # 获取列信息
                    await cur.execute(f"DESCRIBE `{table_name}`")
                    columns = await cur.fetchall()
                    
                    for col in columns:
                        table_info["columns"].append({
                            "name": col[0],
                            "type": col[1],
                            "nullable": col[2] == "YES",
                            "key": col[3],
                            "default": col[4],
                            "extra": col[5]
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
                async with conn.cursor() as cur:
                    # 设置限制
                    await cur.execute(f"SET SESSION max_rows = {limit}")
                    
                    # 执行查询
                    await cur.execute(sql)
                    
                    # 获取列名
                    if cur.description:
                        columns = [desc[0] for desc in cur.description]
                    else:
                        columns = []
                    
                    # 获取数据
                    rows_raw = await cur.fetchmany(limit)
                    rows = [dict(zip(columns, row)) for row in rows_raw]
                    
                    return QueryResult(
                        success=True,
                        columns=columns,
                        rows=rows,
                        total_rows=len(rows),
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
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None
        self.connected = False