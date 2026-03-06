"""
Query History Service
查询历史记录服务
"""
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class QueryHistoryItem:
    """查询历史项"""
    id: str
    query: str
    dialect: str
    generated_sql: str
    datasource: str
    timestamp: str
    favorite: bool = False
    execution_time_ms: int = 0
    success: bool = True
    error: Optional[str] = None


class QueryHistoryService:
    """
    查询历史记录服务
    
    功能：
    1. 保存用户的查询历史
    2. 支持历史查询快速复用
    3. 按时间/数据源筛选
    4. 收藏常用查询
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        初始化服务
        
        Args:
            storage_path: 存储路径，默认 ~/.querycraft/history.json
        """
        if storage_path is None:
            home = os.path.expanduser("~")
            storage_path = os.path.join(home, ".querycraft", "history.json")
        
        self.storage_path = storage_path
        self._ensure_storage_dir()
        self._history: List[QueryHistoryItem] = []
        self._load_history()
    
    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        dir_path = os.path.dirname(self.storage_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
    
    def _load_history(self):
        """加载历史记录"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._history = [QueryHistoryItem(**item) for item in data]
                    logger.info(f"加载了 {len(self._history)} 条历史记录")
        except Exception as e:
            logger.error(f"加载历史记录失败: {e}")
            self._history = []
    
    def _save_history(self):
        """保存历史记录"""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                data = [asdict(item) for item in self._history]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")
    
    def add_query(self, 
                  query: str,
                  dialect: str,
                  generated_sql: str,
                  datasource: str,
                  execution_time_ms: int = 0,
                  success: bool = True,
                  error: Optional[str] = None) -> QueryHistoryItem:
        """
        添加查询记录
        
        Args:
            query: 自然语言查询
            dialect: SQL 方言
            generated_sql: 生成的 SQL
            datasource: 数据源名称
            execution_time_ms: 执行时间（毫秒）
            success: 是否成功
            error: 错误信息
            
        Returns:
            QueryHistoryItem: 新增的历史记录
        """
        import uuid
        
        item = QueryHistoryItem(
            id=str(uuid.uuid4()),
            query=query,
            dialect=dialect,
            generated_sql=generated_sql,
            datasource=datasource,
            timestamp=datetime.utcnow().isoformat(),
            execution_time_ms=execution_time_ms,
            success=success,
            error=error
        )
        
        self._history.insert(0, item)  # 最新在最前面
        
        # 限制历史记录数量
        if len(self._history) > 1000:
            self._history = self._history[:1000]
        
        self._save_history()
        
        return item
    
    def get_history(self, 
                    limit: int = 50,
                    datasource: Optional[str] = None,
                    favorite_only: bool = False) -> List[QueryHistoryItem]:
        """
        获取查询历史
        
        Args:
            limit: 返回数量限制
            datasource: 数据源筛选
            favorite_only: 仅返回收藏的
            
        Returns:
            List[QueryHistoryItem]: 查询历史列表
        """
        result = self._history.copy()
        
        # 筛选数据源
        if datasource:
            result = [item for item in result if item.datasource == datasource]
        
        # 筛选收藏
        if favorite_only:
            result = [item for item in result if item.favorite]
        
        return result[:limit]
    
    def toggle_favorite(self, query_id: str) -> Optional[bool]:
        """
        切换收藏状态
        
        Args:
            query_id: 查询 ID
            
        Returns:
            Optional[bool]: 新的收藏状态，如果未找到返回 None
        """
        for item in self._history:
            if item.id == query_id:
                item.favorite = not item.favorite
                self._save_history()
                return item.favorite
        
        return None
    
    def delete_history(self, query_id: str) -> bool:
        """
        删除单条历史记录
        
        Args:
            query_id: 查询 ID
            
        Returns:
            bool: 是否删除成功
        """
        for i, item in enumerate(self._history):
            if item.id == query_id:
                self._history.pop(i)
                self._save_history()
                return True
        
        return False
    
    def clear_history(self, datasource: Optional[str] = None):
        """
        清除历史记录
        
        Args:
            datasource: 如果指定，仅清除该数据源的历史记录
        """
        if datasource:
            self._history = [item for item in self._history if item.datasource != datasource]
        else:
            self._history = []
        
        self._save_history()
    
    def search_history(self, keyword: str, limit: int = 20) -> List[QueryHistoryItem]:
        """
        搜索历史记录
        
        Args:
            keyword: 搜索关键词
            limit: 返回数量限制
            
        Returns:
            List[QueryHistoryItem]: 匹配的历史记录
        """
        keyword_lower = keyword.lower()
        results = [
            item for item in self._history
            if keyword_lower in item.query.lower() 
            or keyword_lower in item.generated_sql.lower()
        ]
        
        return results[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total = len(self._history)
        favorites = sum(1 for item in self._history if item.favorite)
        successful = sum(1 for item in self._history if item.success)
        failed = total - successful
        
        # 按数据源统计
        by_datasource = defaultdict(int)
        for item in self._history:
            by_datasource[item.datasource] += 1
        
        # 按方言统计
        by_dialect = defaultdict(int)
        for item in self._history:
            by_dialect[item.dialect] += 1
        
        return {
            "total": total,
            "favorites": favorites,
            "successful": successful,
            "failed": failed,
            "by_datasource": dict(by_datasource),
            "by_dialect": dict(by_dialect)
        }


# 全局实例
query_history = QueryHistoryService()
