"""
性能基准测试脚本
用于评估 QueryCraft 的性能优化效果
"""
import asyncio
import time
import requests
import json
from typing import List, Dict, Any
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics


# 配置测试参数
BASE_URL = "http://localhost:8080"
HEADERS = {"Content-Type": "application/json"}

TEST_QUERIES = [
    {
        "query": "查询过去7天的订单总金额和数量",
        "dialect": "mysql",
        "schema_info": {},
        "candidates": 1
    },
    {
        "query": "获取销售金额排名前十的商品",
        "dialect": "mysql", 
        "schema_info": {},
        "candidates": 1
    },
    {
        "query": "统计每个城市的用户注册数量",
        "dialect": "mysql",
        "schema_info": {},
        "candidates": 1
    }
]


def call_generate_api(payload: Dict[str, Any]) -> Dict[str, Any]:
    """调用生成SQL API"""
    url = f"{BASE_URL}/api/v1/generate"
    try:
        response = requests.post(url, headers=HEADERS, data=json.dumps(payload))
        return {
            'success': response.status_code == 200,
            'latency': response.elapsed.total_seconds() * 1000,  # 毫秒
            'status_code': response.status_code,
            'response': response.json() if response.status_code == 200 else response.text
        }
    except Exception as e:
        return {
            'success': False,
            'latency': -1,
            'status_code': -1,
            'error': str(e)
        }


async def performance_test():
    """性能测试函数"""
    print("=" * 60)
    print("QueryCraft 性能基准测试")
    print("=" * 60)
    
    # 测试1: 单次请求性能
    print("\n1. 单次请求性能测试:")
    print("-" * 30)
    
    start_time = time.time()
    for i, test_case in enumerate(TEST_QUERIES):
        result = call_generate_api(test_case)
        print(f"  查询 {i+1}: 延迟 {result['latency']:.2f}ms, 成功: {result['success']}")
    
    elapsed = (time.time() - start_time) * 1000
    print(f"  总耗时: {elapsed:.2f}ms")
    
    # 测试2: 并发性能 
    print("\n2. 并发性能测试 (20并发):")
    print("-" * 30)
    
    # 并发执行多个请求
    num_concurrent = 20
    payloads = [TEST_QUERIES[i % len(TEST_QUERIES)] for i in range(num_concurrent)]
    
    latencies = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
        futures = [executor.submit(call_generate_api, payload) for payload in payloads]
        
        for future in as_completed(futures):
            result = future.result()
            if result['success']:
                latencies.append(result['latency'])
    
    concurrency_elapsed = (time.time() - start_time) * 1000
    if latencies:
        avg_latency = statistics.mean(latencies)
        p95_latency = sorted(latencies)[int(0.95 * len(latencies))] if len(latencies) > 0 else 0
        min_latency = min(latencies)
        max_latency = max(latencies)
        
        print(f"  完成请求数: {len(latencies)}/{num_concurrent}")
        print(f"  并发执行总时间: {concurrency_elapsed:.2f}ms")
        print(f"  平均延迟: {avg_latency:.2f}ms")
        print(f"  P95延迟: {p95_latency:.2f}ms")
        print(f"  最小延迟: {min_latency:.2f}ms")
        print(f"  最大延迟: {max_latency:.2f}ms")
        print(f"  RPS: {len(latencies) / (concurrency_elapsed/1000):.2f}")
        
        # 验证缓存效果 - 用同样的请求做第二次
        print("\n  3. 缓存效果验证（发送重复请求）:")
        print("  -" * 20)
        
        cached_latencies = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=len(payloads)) as executor:
            futures = [executor.submit(call_generate_api, payload) for payload in payloads]
            for future in as_completed(futures):
                result = future.result()
                if result['success']:
                    cached_latencies.append(result['latency'])
        
        cached_elapsed = (time.time() - start_time) * 1000
        if cached_latencies:
            avg_cached_latency = statistics.mean(cached_latencies)
            print(f"    重复请求平均延迟: {avg_cached_latency:.2f}ms (通常比首次请求快)")
            print(f"    预估缓存命中改善: {(avg_latency-avg_cached_latency)/avg_latency*100:.2f}%")
    
    # 测试3: 压力测试
    print("\n4. 持续压力测试 (1分钟):")
    print("-" * 30)
    
    # 定义压力测试函数
    def stress_request(interval_s=0.1) -> List[float]:
        """持续发送请求"""
        results = []
        end_time = time.time() + 30  # 30秒压力测试
        payload = TEST_QUERIES[0]
        
        while time.time() < end_time:
            start_req = time.time()
            result = call_generate_api(payload) 
            request_time = (time.time() - start_req) * 1000
            if result['success']:
                results.append(request_time)
            time.sleep(interval_s)  # 控制请求频率
        
        return results
    
    stress_results = stress_request(interval_s=0.05)  # 每50ms一个请求
    if stress_results:
        print(f"  持续30秒压力测试结果: {len(stress_results)} 个成功请求")
        print(f"  平均延迟: {statistics.mean(stress_results):.2f}ms")
        print(f"  P95延迟: {sorted(stress_results)[int(0.95*len(stress_results))] if stress_results else 0:.2f}ms")
    
    print("\n" + "=" * 60)
    print("性能测试完成")
    print("=" * 60)


def main():
    print("正在测试 QueryCraft 性能优化后的效果...")
    print(f"目标URL: {BASE_URL}/api/v1/generate")
    
    # 检查服务是否可访问
    try:
        health_resp = requests.get(f"{BASE_URL}/api/v1/health")
        if health_resp.status_code == 200:
            print("服务状态: 运行中")
            print(f"版本: {health_resp.json().get('version', 'unknown')}")
        else:
            print("服务状态: 不可用")
    except Exception as e:
        print(f"无法连接到服务: {e}")
        print("\n请确保服务已经在 http://localhost:8080 启动运行")
        return
    
    # 运行性能测试
    asyncio.run(performance_test())


if __name__ == "__main__":
    main()