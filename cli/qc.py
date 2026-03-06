#!/usr/bin/env python3
"""
QueryCraft CLI - 命令行工具
"""

import argparse
import httpx
import json
import sys
from typing import Optional

API_URL = "http://localhost:8080/api/v1"


def generate(query: str, dialect: str = "mysql", datasource: Optional[str] = None):
    """生成SQL"""
    response = httpx.post(
        f"{API_URL}/generate",
        json={
            "query": query,
            "dialect": dialect,
            "datasource": datasource
        },
        timeout=30.0
    )
    
    if response.status_code != 200:
        print(f"错误: {response.status_code}")
        return
    
    result = response.json()
    
    if result["success"]:
        print(f"\n📊 置信度: {result['confidence']}%")
        print(f"⏱️  耗时: {result['duration_ms']}ms")
        print(f"\n🔧 SQL:\n")
        print(result["sql"])
        if result.get("explanation"):
            print(f"\n💡 解释: {result['explanation']}")
    else:
        print(f"❌ 错误: {result.get('error', '未知错误')}")


def validate(sql: str, dialect: str = "mysql"):
    """验证SQL"""
    response = httpx.post(
        f"{API_URL}/validate",
        json={
            "sql": sql,
            "dialect": dialect
        },
        timeout=30.0
    )
    
    if response.status_code != 200:
        print(f"错误: {response.status_code}")
        return
    
    result = response.json()
    
    print(f"\n📊 总分: {result['score']}%")
    print(f"   语法: {result['syntax_score']}%")
    print(f"   语义: {result['semantic_score']}%")
    print(f"   安全: {result['security_score']}%")
    
    if result["errors"]:
        print("\n❌ 错误:")
        for err in result["errors"]:
            print(f"   - {err}")
    
    if result["warnings"]:
        print("\n⚠️  警告:")
        for warn in result["warnings"]:
            print(f"   - {warn}")
    
    if result["valid"]:
        print("\n✅ SQL 有效")


def health():
    """健康检查"""
    response = httpx.get(f"{API_URL}/health", timeout=5.0)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ {result['status']}")
        print(f"   版本: {result['version']}")
        print(f"   LLM: {result['llm_provider']}")
    else:
        print("❌ 服务不可用")


def main():
    parser = argparse.ArgumentParser(
        description="QueryCraft - 自然语言转SQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  qc generate "查询最近7天的订单数量"
  qc generate "统计每个部门的员工数量" --dialect postgresql
  qc validate "SELECT * FROM users"
  qc health
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # generate 命令
    gen_parser = subparsers.add_parser("generate", help="生成SQL")
    gen_parser.add_argument("query", help="自然语言查询")
    gen_parser.add_argument("--dialect", "-d", default="mysql", 
                           choices=["mysql", "postgresql", "hive", "spark", "flink"],
                           help="SQL方言")
    gen_parser.add_argument("--datasource", "-ds", help="数据源名称")
    
    # validate 命令
    val_parser = subparsers.add_parser("validate", help="验证SQL")
    val_parser.add_argument("sql", help="待验证的SQL")
    val_parser.add_argument("--dialect", "-d", default="mysql", help="SQL方言")
    
    # health 命令
    subparsers.add_parser("health", help="健康检查")
    
    args = parser.parse_args()
    
    if args.command == "generate":
        generate(args.query, args.dialect, args.datasource)
    elif args.command == "validate":
        validate(args.sql, args.dialect)
    elif args.command == "health":
        health()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()