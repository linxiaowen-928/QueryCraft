"""
MySQL 连接器
"""
import asyncio
from asyncio import Semaphore

import aiomysql
from typing import Dict, Any, List, Optional
import time
# 添加连接信号量，控制并发连接数
MAX_CONNECTIONS = 20  # 最大并发数据库连接数
CONNECTION_SEMAPHORE = Semaphore(MAX_CONNECTIONS)
# 连接统计计数器
active_connections = 0
peak_connections = 0


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
                minsize=5,  # 从1改为5，增加最小连接数
                maxsize=20,  # 从10改为20，增加最大连接数
                pool_recycle=3600,  # 添加连接回收周期（1小时）
                pool_timeout=10,  # 添加连接超时
                loop=None # 使用默认事件循环
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
        
        # 使用模块级别的连接信号量控制并发
        async with CONNECTION_SEMAPHORE:  # 控制最大并发连接数
            try:
                async with self.pool.acquire() as conn:
                    async with conn.cursor(aiomysql.DictCursor) as cur:  # 使用字典游标提高数据处理效率
                        # 设置限制
                        await cur.execute(f"SET SESSION max_rows = {limit}")
                        
                        # 执行查询
                        await cur.execute(sql)
                        
                        # 获取列名
                        if cur.description:
                            columns = [desc[0] for desc in cur.description]
                        else:
                            columns = []
                        
                        # 一次性批量获取所有数据，而不是分批获取
                        rows = await cur.fetchall()
                        if limit and len(rows) > limit:
                            rows = rows[:limit]
                        
                        # 将结果转换为字典列表（已在游标层面完成）
                        rows_as_dicts = [dict(row) for row in rows]
                        
                        return QueryResult(
                            success=True,
                            columns=columns,
                            rows=rows_as_dicts,
                            total_rows=len(rows_as_dicts),
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

    async def get_database_name(self) -> str:
        """获取数据库名称"""
        return self.config.database

    async def get_tables(self) -> List[str]:
        """获取所有表名"""
        if not self.pool:
            raise RuntimeError("Not connected")
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SHOW TABLES")
                tables = await cur.fetchall()
                return [table[0] for table in tables]

    async def get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """获取表的列信息"""
        if not self.pool:
            raise RuntimeError("Not connected")
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 获取列信息
                await cur.execute(f"DESCRIBE `{table_name}`")
                columns = await cur.fetchall()
                
                result = []
                for col in columns:
                    result.append({
                        "name": col[0],
                        "type": col[1],
                        "nullable": col[2] == "YES",
                        "is_primary_key": col[3] == "PRI",
                        "is_foreign_key": col[3] == "MUL",
                        "default": col[4],
                        "comment": col[5] if len(col) > 5 else None
                    })
                
                return result

    async def get_table_comment(self, table_name: str) -> Optional[str]:
        """获取表的注释"""
        if not self.pool:
            raise RuntimeError("Not connected")
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                sql = f"""
                    SELECT TABLE_COMMENT 
                    FROM information_schema.TABLES 
                    WHERE TABLE_SCHEMA = '{self.config.database}' 
                    AND TABLE_NAME = '{table_name}'
                """
                await cur.execute(sql)
                result = await cur.fetchone()
                return result[0] if result else None