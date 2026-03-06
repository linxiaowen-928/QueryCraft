"""
SQL生成服务
"""

import time
import httpx
from typing import Optional, List, Dict, Any
from app.config import settings


class SQLGenerator:
    """SQL生成器"""
    
    def __init__(self):
        self.provider = settings.llm_provider
        self.model = settings.llm_model
        self.api_key = settings.llm_api_key
        self.api_url = settings.llm_api_url
    
    async def generate(
        self,
        query: str,
        dialect: str = "mysql",
        schema_info: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        candidates: int = 1
    ) -> Dict[str, Any]:
        """生成SQL"""
        
        start_time = time.time()
        
        try:
            # 构建提示词
            system_prompt = self._build_system_prompt(dialect, schema_info, context)
            user_prompt = self._build_user_prompt(query)
            
            # 调用LLM
            if self.api_key:
                response_text = await self._call_llm(system_prompt, user_prompt)
            else:
                response_text = self._mock_response(query, dialect)
            
            # 解析响应
            sql = self._parse_sql(response_text)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return {
                "success": True,
                "sql": sql,
                "confidence": self._calculate_confidence(sql, schema_info),
                "explanation": self._generate_explanation(sql, query),
                "duration_ms": duration_ms
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "duration_ms": int((time.time() - start_time) * 1000)
            }
    
    def _build_system_prompt(
        self,
        dialect: str,
        schema_info: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """构建系统提示词"""
        
        prompt = f"""你是一个专业的SQL生成助手。将用户的自然语言查询转换为{dialect}方言的SQL语句。

## 输出规则
1. 只输出SQL语句，不要包含解释
2. SQL必须是有效的{dialect}语法
3. 使用适当的表别名提高可读性
4. 对于复杂查询，添加适当的注释

## 安全规则
1. 不要生成DROP、TRUNCATE语句
2. DELETE和UPDATE必须有WHERE条件
3. 不要尝试访问系统表"""
        
        if schema_info:
            prompt += "\n\n## 数据库结构\n"
            prompt += self._format_schema(schema_info)
        
        if context:
            if context.get("business_definitions"):
                prompt += "\n\n## 业务口径定义\n"
                for key, value in context["business_definitions"].items():
                    prompt += f"- {key}: {value}\n"
            
            if context.get("business_rules"):
                prompt += "\n\n## 业务规范\n"
                for rule in context["business_rules"]:
                    prompt += f"- {rule}\n"
        
        return prompt
    
    def _build_user_prompt(self, query: str) -> str:
        """构建用户提示词"""
        return f"请将以下自然语言查询转换为SQL：\n\n{query}"
    
    def _format_schema(self, schema_info: Dict[str, Any]) -> str:
        """格式化Schema信息"""
        result = []
        
        if "tables" in schema_info:
            for table in schema_info["tables"]:
                table_name = table.get("name", "unknown")
                comment = table.get("comment", "")
                columns = table.get("columns", [])
                
                col_strs = []
                for col in columns:
                    col_str = f"{col.get('name')} {col.get('type')}"
                    if col.get("comment"):
                        col_str += f" -- {col.get('comment')}"
                    col_strs.append(col_str)
                
                result.append(
                    f"表 {table_name}{' -- ' + comment if comment else ''}:\n  " +
                    "\n  ".join(col_strs)
                )
        
        if "database" in schema_info:
            result.insert(0, f"数据库: {schema_info['database']}")
        
        return "\n\n".join(result)
    
    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """调用LLM API - 支持 ZhipuAI"""
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # ZhipuAI 使用 Authorization: Bearer
        if self.provider == "zhipuai":
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 1000
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                error_detail = response.text
                raise Exception(f"LLM API error ({response.status_code}): {error_detail}")
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    def _mock_response(self, query: str, dialect: str) -> str:
        """模拟响应（无API Key时）"""
        return f"-- 模拟SQL（未配置API Key）\nSELECT * FROM table_name WHERE 1=1 LIMIT 100;"
    
    def _parse_sql(self, response: str) -> str:
        """解析SQL响应"""
        sql = response.strip()
        if sql.startswith("```sql"):
            sql = sql[6:]
        elif sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]
        return sql.strip()
    
    def _calculate_confidence(self, sql: str, schema_info: Optional[Dict[str, Any]]) -> int:
        """计算置信度"""
        base_confidence = 70
        
        if "WHERE" in sql.upper():
            base_confidence += 5
        if "JOIN" in sql.upper():
            base_confidence += 3
        if "GROUP BY" in sql.upper():
            base_confidence += 3
        if sql.count("SELECT") > 1:
            base_confidence -= 5
        
        return min(100, max(0, base_confidence))
    
    def _generate_explanation(self, sql: str, query: str) -> str:
        """生成SQL解释"""
        return f"根据查询 '{query}' 生成的SQL语句"


# 单例
generator = SQLGenerator()