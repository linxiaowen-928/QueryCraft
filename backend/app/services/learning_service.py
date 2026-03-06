"""
Learning Service
历史经验学习服务

功能：
1. 从用户反馈中学习
2. 积累业务术语与数据库字段的映射
3. 支持跨会话的知识持久化
"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class LearnedKnowledge:
    """学习到的知识"""
    id: str
    key_term: str  # 业务术语
    mapped_table: str  # 映射的表
    mapped_field: Optional[str] = None  # 映射的字段
    description: Optional[str] = None  # 描述
    confidence: float = 1.0  # 置信度
    usage_count: int = 0  # 使用次数
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class UserFeedback:
    """用户反馈"""
    id: str
    query: str
    original_sql: str
    corrected_sql: Optional[str] = None
    feedback_text: Optional[str] = None
    datasource: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class SessionContext:
    """会话上下文"""
    session_id: str
    datasource: str
    user_provided_context: Dict[str, Any] = field(default_factory=dict)
    learned_mappings: List[str] = field(default_factory=list)  # 知识ID列表
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_active: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class LearningService:
    """
    历史经验学习服务
    
    功能：
    1. 记录用户的反馈和修正
    2. 将反馈转化为可复用的知识
    3. 建立业务术语与数据库字段的映射关系
    4. 支持跨会话的知识持久化
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        初始化服务
        
        Args:
            storage_dir: 存储目录，默认 ~/.querycraft/
        """
        if storage_dir is None:
            home = os.path.expanduser("~")
            storage_dir = os.path.join(home, ".querycraft")
        
        self.storage_dir = storage_dir
        self._ensure_storage_dir()
        
        # 知识库
        self.knowledge_file = os.path.join(storage_dir, "knowledge.json")
        self.feedback_file = os.path.join(storage_dir, "feedback.json")
        self.sessions_file = os.path.join(storage_dir, "sessions.json")
        
        # 内存中的数据
        self._knowledge: List[LearnedKnowledge] = []
        self._feedback: List[UserFeedback] = []
        self._sessions: Dict[str, SessionContext] = {}
        
        # 加载数据
        self._load_data()
    
    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
    
    def _load_data(self):
        """加载数据"""
        # 加载知识库
        try:
            if os.path.exists(self.knowledge_file):
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._knowledge = [LearnedKnowledge(**item) for item in data]
                    logger.info(f"加载了 {len(self._knowledge)} 条知识")
        except Exception as e:
            logger.error(f"加载知识库失败: {e}")
        
        # 加载反馈
        try:
            if os.path.exists(self.feedback_file):
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._feedback = [UserFeedback(**item) for item in data]
                    logger.info(f"加载了 {len(self._feedback)} 条反馈")
        except Exception as e:
            logger.error(f"加载反馈失败: {e}")
        
        # 加载会话
        try:
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._sessions = {k: SessionContext(**v) for k, v in data.items()}
                    logger.info(f"加载了 {len(self._sessions)} 个会话")
        except Exception as e:
            logger.error(f"加载会话失败: {e}")
    
    def _save_knowledge(self):
        """保存知识库"""
        try:
            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                data = [asdict(item) for item in self._knowledge]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存知识库失败: {e}")
    
    def _save_feedback(self):
        """保存反馈"""
        try:
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                data = [asdict(item) for item in self._feedback]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存反馈失败: {e}")
    
    def _save_sessions(self):
        """保存会话"""
        try:
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                data = {k: asdict(v) for k, v in self._sessions.items()}
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存会话失败: {e}")
    
    # ==================== 用户反馈 ====================
    
    def add_feedback(self,
                    query: str,
                    original_sql: str,
                    corrected_sql: Optional[str] = None,
                    feedback_text: Optional[str] = None,
                    datasource: str = "") -> UserFeedback:
        """
        添加用户反馈
        
        Args:
            query: 用户查询
            original_sql: 原始生成的 SQL
            corrected_sql: 用户修正的 SQL
            feedback_text: 反馈文本
            datasource: 数据源名称
            
        Returns:
            UserFeedback: 新增的反馈
        """
        import uuid
        
        feedback = UserFeedback(
            id=str(uuid.uuid4()),
            query=query,
            original_sql=original_sql,
            corrected_sql=corrected_sql,
            feedback_text=feedback_text,
            datasource=datasource
        )
        
        self._feedback.insert(0, feedback)
        
        # 如果有修正，自动提取知识
        if corrected_sql and corrected_sql != original_sql:
            self._extract_knowledge_from_correction(query, original_sql, corrected_sql, datasource)
        
        # 限制反馈数量
        if len(self._feedback) > 1000:
            self._feedback = self._feedback[:1000]
        
        self._save_feedback()
        
        return feedback
    
    def _extract_knowledge_from_correction(self, query: str, original_sql: str, 
                                          corrected_sql: str, datasource: str):
        """
        从修正中提取知识
        
        例如：
        - 用户说"订单表应该是orders而不是order"
        - 系统学习到：order -> orders
        """
        # 简化实现：提取表名差异
        original_tables = self._extract_table_names(original_sql)
        corrected_tables = self._extract_table_names(corrected_sql)
        
        # 如果表名不同，学习映射
        if original_tables and corrected_tables:
            for orig, corr in zip(original_tables, corrected_tables):
                if orig != corr:
                    self.add_knowledge(
                        key_term=orig,
                        mapped_table=corr,
                        description=f"从用户反馈学习：'{orig}' 应改为 '{corr}'",
                        source="feedback_correction"
                    )
    
    def _extract_table_names(self, sql: str) -> List[str]:
        """提取 SQL 中的表名（简化实现）"""
        import re
        # 简单的正则匹配 FROM 和 JOIN 后的表名
        pattern = r'(?:FROM|JOIN)\s+`?(\w+)`?'
        matches = re.findall(pattern, sql, re.IGNORECASE)
        return matches
    
    def get_feedback(self, limit: int = 50, datasource: Optional[str] = None) -> List[UserFeedback]:
        """
        获取反馈列表
        
        Args:
            limit: 返回数量限制
            datasource: 数据源筛选
            
        Returns:
            List[UserFeedback]: 反馈列表
        """
        result = self._feedback.copy()
        
        if datasource:
            result = [f for f in result if f.datasource == datasource]
        
        return result[:limit]
    
    # ==================== 知识库 ====================
    
    def add_knowledge(self,
                     key_term: str,
                     mapped_table: str,
                     mapped_field: Optional[str] = None,
                     description: Optional[str] = None,
                     confidence: float = 0.8,
                     source: str = "manual") -> LearnedKnowledge:
        """
        添加知识
        
        Args:
            key_term: 业务术语
            mapped_table: 映射的表
            mapped_field: 映射的字段
            description: 描述
            confidence: 置信度
            source: 来源
            
        Returns:
            LearnedKnowledge: 新增的知识
        """
        import uuid
        
        # 检查是否已存在
        existing = self._find_knowledge(key_term)
        if existing:
            # 更新现有知识
            existing.mapped_table = mapped_table
            existing.mapped_field = mapped_field
            existing.description = description
            existing.confidence = min(1.0, existing.confidence + 0.1)
            existing.usage_count += 1
            existing.updated_at = datetime.utcnow().isoformat()
            self._save_knowledge()
            return existing
        
        # 创建新知识
        knowledge = LearnedKnowledge(
            id=str(uuid.uuid4()),
            key_term=key_term,
            mapped_table=mapped_table,
            mapped_field=mapped_field,
            description=description,
            confidence=confidence
        )
        
        self._knowledge.append(knowledge)
        self._save_knowledge()
        
        return knowledge
    
    def _find_knowledge(self, key_term: str) -> Optional[LearnedKnowledge]:
        """查找知识"""
        for k in self._knowledge:
            if k.key_term.lower() == key_term.lower():
                return k
        return None
    
    def get_knowledge(self, 
                      limit: int = 50,
                      min_confidence: float = 0.0) -> List[LearnedKnowledge]:
        """
        获取知识列表
        
        Args:
            limit: 返回数量限制
            min_confidence: 最低置信度筛选
            
        Returns:
            List[LearnedKnowledge]: 知识列表
        """
        result = [k for k in self._knowledge if k.confidence >= min_confidence]
        # 按置信度和使用次数排序
        result.sort(key=lambda x: (x.confidence, x.usage_count), reverse=True)
        return result[:limit]
    
    def search_knowledge(self, keyword: str) -> List[LearnedKnowledge]:
        """
        搜索知识
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            List[LearnedKnowledge]: 匹配的知识
        """
        keyword_lower = keyword.lower()
        return [
            k for k in self._knowledge
            if keyword_lower in k.key_term.lower()
            or keyword_lower in k.mapped_table.lower()
            or (k.description and keyword_lower in k.description.lower())
        ]
    
    def delete_knowledge(self, knowledge_id: str) -> bool:
        """
        删除知识
        
        Args:
            knowledge_id: 知识 ID
            
        Returns:
            bool: 是否删除成功
        """
        for i, k in enumerate(self._knowledge):
            if k.id == knowledge_id:
                self._knowledge.pop(i)
                self._save_knowledge()
                return True
        return False
    
    # ==================== 会话管理 ====================
    
    def create_session(self, session_id: str, datasource: str) -> SessionContext:
        """
        创建会话
        
        Args:
            session_id: 会话 ID
            datasource: 数据源名称
            
        Returns:
            SessionContext: 新建的会话
        """
        session = SessionContext(
            session_id=session_id,
            datasource=datasource
        )
        
        self._sessions[session_id] = session
        self._save_sessions()
        
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """
        获取会话
        
        Args:
            session_id: 会话 ID
            
        Returns:
            Optional[SessionContext]: 会话，如果不存在返回 None
        """
        return self._sessions.get(session_id)
    
    def update_session_context(self, session_id: str, context: Dict[str, Any]):
        """
        更新会话上下文
        
        Args:
            session_id: 会话 ID
            context: 新的上下文
        """
        session = self._sessions.get(session_id)
        if session:
            session.user_provided_context.update(context)
            session.last_active = datetime.utcnow().isoformat()
            self._save_sessions()
    def add_session_knowledge(self, session_id: str, knowledge_id: str):
        """
        为会话添加知识引用
        
        Args:
            session_id: 会话 ID
            knowledge_id: 知识 ID
        """
        session = self._sessions.get(session_id)
        if session and knowledge_id not in session.learned_mappings:
            session.learned_mappings.append(knowledge_id)
            session.last_active = datetime.utcnow().isoformat()
            self._save_sessions()
    
    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话的完整上下文（用于 SQL 生成）
        
        Args:
            session_id: 会话 ID
            
        Returns:
            Dict[str, Any]: 包含知识映射的上下文
        """
        session = self._sessions.get(session_id)
        if not session:
            return {}
        
        # 获取会话关联的知识
        knowledge_list = []
        for kid in session.learned_mappings:
            for k in self._knowledge:
                if k.id == kid:
                    knowledge_list.append(k)
        
        # 也添加高置信度的全局知识
        global_knowledge = self.get_knowledge(min_confidence=0.5)
        
        return {
            "session_id": session_id,
            "datasource": session.datasource,
            "user_context": session.user_provided_context,
            "session_knowledge": [asdict(k) for k in knowledge_list],
            "global_knowledge": [asdict(k) for k in global_knowledge[:10]],
            "table_mappings": self._build_table_mappings(knowledge_list + global_knowledge)
        }
    
    def _build_table_mappings(self, knowledge_list: List[LearnedKnowledge]) -> Dict[str, str]:
        """构建表名映射字典"""
        mappings = {}
        for k in knowledge_list:
            if k.mapped_table:
                mappings[k.key_term] = k.mapped_table
        return mappings
    
    # ==================== 统计 ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_knowledge = len(self._knowledge)
        high_confidence = sum(1 for k in self._knowledge if k.confidence >= 0.8)
        total_feedback = len(self._feedback)
        total_sessions = len(self._sessions)
        
        # 按来源统计知识
        # (简化版本，没有tracking source)
        
        return {
            "total_knowledge": total_knowledge,
            "high_confidence_knowledge": high_confidence,
            "total_feedback": total_feedback,
            "total_sessions": total_sessions,
            "average_confidence": sum(k.confidence for k in self._knowledge) / total_knowledge if total_knowledge > 0 else 0
        }


# 全局实例
learning_service = LearningService()
