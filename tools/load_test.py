#!/usr/bin/env python3
"""Simple load-test helper for petra-gpt-service.

Usage:
  python tools/load_test.py --url http://localhost:8000/health --concurrency 10 --requests 100

This script is intentionally small: it fires concurrent HTTP requests (GET or POST) and reports basic timing stats.
"""
import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests


def worker(session, method, url, payload=None, timeout=10):
    start = time.time()
    try:
        if method == 'GET':
            r = session.get(url, timeout=timeout)
        else:
            r = session.post(url, json=payload or {}, timeout=timeout)
        latency = time.time() - start
        return (r.status_code, latency)
    except Exception as e:
        return (None, time.time() - start)


def run_load(url, method, concurrency, total_requests):
    session = requests.Session()
    results = []
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = [ex.submit(worker, session, method, url) for _ in range(total_requests)]
        for f in as_completed(futures):
            results.append(f.result())
    statuses = [r[0] for r in results]
    latencies = [r[1] for r in results if r[1] is not None]
    success = sum(1 for s in statuses if s and 200 <= s < 400)
    print(f"Total: {len(results)}, Success: {success}, Failures: {len(results)-success}")
    if latencies:
        print(f"Latency ms: p50={percentile(latencies,50)*1000:.1f} p95={percentile(latencies,95)*1000:.1f} avg={sum(latencies)/len(latencies)*1000:.1f}")


def percentile(data, p):
    data = sorted(data)
    k = (len(data)-1) * (p/100)
    f = int(k)
    c = min(f+1, len(data)-1)
    if f == c:
        return data[int(k)]
    d0 = data[f] * (c - k)
    d1 = data[c] * (k - f)
    return d0 + d1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True, help='Target URL')
    parser.add_argument('--method', default='GET', choices=['GET','POST'])
    parser.add_argument('--concurrency', type=int, default=5)
    parser.add_argument('--requests', type=int, default=50)
    args = parser.parse_args()
    run_load(args.url, args.method, args.concurrency, args.requests)


if __name__ == '__main__':
    main()
