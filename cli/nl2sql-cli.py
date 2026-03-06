#!/usr/bin/env python3
"""
NL2SQL CLI - 命令行工具

用法:
    nl2sql "查询最近30天的订单总金额" --dialect mysql
    nl2sql validate "SELECT * FROM users" --dialect mysql
    nl2sql serve --port 8080
"""

import argparse
import sys
import json
import httpx
from typing import Optional


DEFAULT_API_URL = "http://localhost:8080/api/v1"


def generate_sql(query: str, dialect: str = "mysql", api_url: str = DEFAULT_API_URL) -> dict:
    """生成 SQL"""
    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            f"{api_url}/generate",
            json={
                "query": query,
                "dialect": dialect
            }
        )
        return response.json()


def validate_sql(sql: str, dialect: str = "mysql", api_url: str = DEFAULT_API_URL) -> dict:
    """验证 SQL"""
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            f"{api_url}/validate",
            json={
                "sql": sql,
                "dialect": dialect
            }
        )
        return response.json()


def check_health(api_url: str = DEFAULT_API_URL) -> dict:
    """检查服务健康"""
    with httpx.Client(timeout=10.0) as client:
        response = client.get(f"{api_url}/health")
        return response.json()


def main():
    parser = argparse.ArgumentParser(
        prog="nl2sql",
        description="NL2SQL - 自然语言转SQL命令行工具"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # generate 命令
    gen_parser = subparsers.add_parser("generate", aliases=["gen", "g"], help="生成SQL")
    gen_parser.add_argument("query", help="自然语言查询")
    gen_parser.add_argument("--dialect", "-d", default="mysql", 
                           help="SQL方言 (mysql, postgresql, hive, spark)")
    gen_parser.add_argument("--api-url", default=DEFAULT_API_URL, help="API地址")
    gen_parser.add_argument("--json", "-j", action="store_true", help="JSON输出")
    
    # validate 命令
    val_parser = subparsers.add_parser("validate", aliases=["val", "v"], help="验证SQL")
    val_parser.add_argument("sql", help="SQL语句")
    val_parser.add_argument("--dialect", "-d", default="mysql", help="SQL方言")
    val_parser.add_argument("--api-url", default=DEFAULT_API_URL, help="API地址")
    val_parser.add_argument("--json", "-j", action="store_true", help="JSON输出")
    
    # health 命令
    health_parser = subparsers.add_parser("health", help="检查服务健康")
    health_parser.add_argument("--api-url", default=DEFAULT_API_URL, help="API地址")
    
    # 直接查询（无子命令）
    parser.add_argument("query", nargs="?", help="自然语言查询（简写）")
    parser.add_argument("--dialect", "-d", default="mysql", help="SQL方言")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="API地址")
    
    args = parser.parse_args()
    
    # 直接查询模式
    if args.query and not args.command:
        result = generate_sql(args.query, args.dialect, args.api_url)
        if result.get("success"):
            print(result.get("sql", ""))
        else:
            print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
            sys.exit(1)
        return
    
    # 子命令模式
    if args.command in ["generate", "gen", "g"]:
        result = generate_sql(args.query, args.dialect, args.api_url)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            if result.get("success"):
                print("SQL:")
                print(result.get("sql", ""))
                print(f"\n置信度: {result.get('confidence', 0)}%")
                print(f"耗时: {result.get('duration_ms', 0)}ms")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
                sys.exit(1)
    
    elif args.command in ["validate", "val", "v"]:
        result = validate_sql(args.sql, args.dialect, args.api_url)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            status = "✅ 有效" if result.get("valid") else "❌ 无效"
            print(f"状态: {status}")
            print(f"总分: {result.get('score', 0)}")
            print(f"语法: {result.get('syntax_score', 0)}")
            print(f"语义: {result.get('semantic_score', 0)}")
            print(f"安全: {result.get('security_score', 0)}")
            if result.get("errors"):
                print("\n错误:")
                for err in result["errors"]:
                    print(f"  - {err}")
            if result.get("warnings"):
                print("\n警告:")
                for warn in result["warnings"]:
                    print(f"  - {warn}")
    
    elif args.command == "health":
        result = check_health(args.api_url)
        print(f"状态: {result.get('status', 'unknown')}")
        print(f"版本: {result.get('version', 'unknown')}")
        print(f"LLM: {result.get('llm_provider', 'unknown')}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()