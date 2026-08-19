"""
Performance and Load Testing Benchmark Suite for Financial Fraud Detection Platform.
Executes concurrent benchmark tests across key API endpoints and measures throughput,
average, median, p95, and p99 latency distributions.
"""

import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np

# Ensure workspace root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

# Realistic single transaction payload
SAMPLE_PREDICT_PAYLOAD = {
    "transaction": {
        "transaction_id": "T_BENCH_001",
        "customer_id": "CUST_BENCH_01",
        "transaction_date": "14-08-2026 14:30",
        "transaction_amount": 550.0,
        "merchant_category": "Travel",
        "payment_method": "Credit Card",
        "device_type": "POS",
        "location": "Bengaluru",
        "is_international": 1,
        "previous_transactions": 5,
        "average_spend": 40.0,
        "account_age_days": 45,
        "suspicious_keyword": "Yes"
    }
}

# Realistic batch transaction payload (10 items)
SAMPLE_BATCH_PAYLOAD = {
    "transactions": [
        {
            "transaction_id": f"T_BATCH_{i:04d}",
            "customer_id": f"CUST_BATCH_{i:04d}",
            "transaction_date": "14-08-2026 14:30",
            "transaction_amount": 100.0 + (i * 25.0),
            "merchant_category": "Travel" if i % 2 == 0 else "Grocery",
            "payment_method": "Credit Card" if i % 2 == 0 else "Debit Card",
            "device_type": "POS" if i % 2 == 0 else "Mobile",
            "location": "Bengaluru",
            "is_international": i % 2,
            "previous_transactions": 10 + i,
            "average_spend": 50.0,
            "account_age_days": 100 + i,
            "suspicious_keyword": "Yes" if i % 3 == 0 else "No"
        }
        for i in range(10)
    ]
}


def make_request(method: str, endpoint: str, json_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Execute single request and measure latency."""
    t0 = time.perf_counter()
    try:
        if method == "GET":
            resp = client.get(endpoint)
        elif method == "POST":
            resp = client.post(endpoint, json=json_data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        latency_ms = (time.perf_counter() - t0) * 1000.0
        success = (resp.status_code in [200, 201])
        return {
            "success": success,
            "status_code": resp.status_code,
            "latency_ms": latency_ms
        }
    except Exception as e:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "success": False,
            "status_code": 500,
            "latency_ms": latency_ms,
            "error": str(e)
        }


def benchmark_endpoint(
    name: str,
    method: str,
    endpoint: str,
    json_data: Dict[str, Any] = None,
    total_requests: int = 100,
    concurrency: int = 10
) -> Dict[str, Any]:
    """Runs concurrent load test on specified endpoint."""
    print(f"\n[Benchmarking] {name} ({method} {endpoint}) - {total_requests} requests @ concurrency={concurrency}...")

    # Warmup request
    make_request(method, endpoint, json_data)

    latencies = []
    successes = 0
    failures = 0

    t_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(make_request, method, endpoint, json_data)
            for _ in range(total_requests)
        ]
        for f in as_completed(futures):
            res = f.result()
            latencies.append(res["latency_ms"])
            if res["success"]:
                successes += 1
            else:
                failures += 1

    total_wall_time = time.perf_counter() - t_start
    rps = total_requests / total_wall_time if total_wall_time > 0 else 0.0

    lat_arr = np.array(latencies)
    avg_lat = float(np.mean(lat_arr))
    median_lat = float(np.median(lat_arr))
    p95_lat = float(np.percentile(lat_arr, 95))
    p99_lat = float(np.percentile(lat_arr, 99))
    min_lat = float(np.min(lat_arr))
    max_lat = float(np.max(lat_arr))
    error_rate = (failures / total_requests) * 100.0

    result = {
        "endpoint": endpoint,
        "method": method,
        "total_requests": total_requests,
        "concurrency": concurrency,
        "successful_requests": successes,
        "failed_requests": failures,
        "error_rate_pct": round(error_rate, 2),
        "total_time_seconds": round(total_wall_time, 4),
        "requests_per_second": round(rps, 2),
        "min_latency_ms": round(min_lat, 2),
        "avg_latency_ms": round(avg_lat, 2),
        "median_latency_ms": round(median_lat, 2),
        "p95_latency_ms": round(p95_lat, 2),
        "p99_latency_ms": round(p99_lat, 2),
        "max_latency_ms": round(max_lat, 2)
    }

    print(f"  -> RPS: {rps:.2f} req/s | Avg: {avg_lat:.2f}ms | Median: {median_lat:.2f}ms | p95: {p95_lat:.2f}ms | p99: {p99_lat:.2f}ms | Errors: {error_rate:.1f}%")
    return result


def run_all_performance_tests() -> Dict[str, Any]:
    """Execute complete performance benchmark suite."""
    print("=" * 70)
    print("FINANCIAL FRAUD DETECTION - PERFORMANCE & LATENCY BENCHMARK SUITE")
    print("=" * 70)

    benchmarks = [
        {"name": "Health Liveness Check", "method": "GET", "endpoint": "/health", "data": None, "reqs": 200, "conc": 10},
        {"name": "Readiness Probe Check", "method": "GET", "ready_endpoint": "/ready", "endpoint": "/ready", "data": None, "reqs": 100, "conc": 10},
        {"name": "Transactions List Query", "method": "GET", "endpoint": "/transactions?limit=20", "data": None, "reqs": 100, "conc": 10},
        {"name": "Analytics Summary Calculation", "method": "GET", "endpoint": "/analytics/summary", "data": None, "reqs": 100, "conc": 10},
        {"name": "Single Transaction Prediction", "method": "POST", "endpoint": "/predictions/predict", "data": SAMPLE_PREDICT_PAYLOAD, "reqs": 100, "conc": 10},
        {"name": "Batch Prediction (10 TX/req)", "method": "POST", "endpoint": "/predictions/batch", "data": SAMPLE_BATCH_PAYLOAD, "reqs": 50, "conc": 5}
    ]

    all_results = {}
    for bench in benchmarks:
        ep_name = bench["name"]
        res = benchmark_endpoint(
            name=ep_name,
            method=bench["method"],
            endpoint=bench["endpoint"],
            json_data=bench["data"],
            total_requests=bench["reqs"],
            concurrency=bench["conc"]
        )
        all_results[ep_name] = res

    # Save results to reports
    reports_dir = BASE_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / "performance_test_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n[Artifact Saved] JSON Results: {json_path}")

    # Generate Markdown Report
    md_path = reports_dir / "performance_test_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# API Performance & Latency Benchmark Report\n\n")
        f.write(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("| Endpoint / Operation | Method | Requests | Concurrency | RPS (req/s) | Avg Latency (ms) | Median (ms) | p95 (ms) | p99 (ms) | Error Rate (%) |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|\n")
        for name, r in all_results.items():
            f.write(f"| **{name}** (`{r['endpoint']}`) | `{r['method']}` | {r['total_requests']} | {r['concurrency']} | {r['requests_per_second']} | {r['avg_latency_ms']} | {r['median_latency_ms']} | {r['p95_latency_ms']} | {r['p99_latency_ms']} | {r['error_rate_pct']}% |\n")
    print(f"[Artifact Saved] Markdown Report: {md_path}")

    print("\n" + "=" * 70)
    print("BENCHMARK SUITE COMPLETED SUCCESSFULLY.")
    print("=" * 70)
    return all_results


if __name__ == "__main__":
    run_all_performance_tests()
