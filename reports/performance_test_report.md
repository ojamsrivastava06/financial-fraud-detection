# API Performance & Latency Benchmark Report

Generated on: 2026-08-16 19:21:36

| Endpoint / Operation | Method | Requests | Concurrency | RPS (req/s) | Avg Latency (ms) | Median (ms) | p95 (ms) | p99 (ms) | Error Rate (%) |
|---|---|---|---|---|---|---|---|---|---|
| **Health Liveness Check** (`/health`) | `GET` | 200 | 10 | 74.68 | 130.62 | 125.78 | 177.07 | 217.65 | 0.0% |
| **Readiness Probe Check** (`/ready`) | `GET` | 100 | 10 | 56.52 | 171.95 | 169.06 | 219.02 | 231.46 | 0.0% |
| **Transactions List Query** (`/transactions?limit=20`) | `GET` | 100 | 10 | 44.21 | 221.06 | 225.56 | 287.88 | 294.62 | 0.0% |
| **Analytics Summary Calculation** (`/analytics/summary`) | `GET` | 100 | 10 | 39.92 | 245.33 | 165.21 | 1006.45 | 1032.56 | 0.0% |
| **Single Transaction Prediction** (`/predictions/predict`) | `POST` | 100 | 10 | 15.49 | 637.13 | 645.54 | 871.18 | 977.74 | 0.0% |
| **Batch Prediction (10 TX/req)** (`/predictions/batch`) | `POST` | 50 | 5 | 2.25 | 2199.15 | 2187.22 | 2940.53 | 3174.03 | 0.0% |
