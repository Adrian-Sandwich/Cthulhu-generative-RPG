# Local load test

UTC: 2026-09-25T02:03:01.223119+00:00

Profile: capacity; model: simulated; servers: 2; threads/server: 16; simulated generation: 3.0 s.

Real HTTP + PostgreSQL. Closed-loop clients, no think time. Setup excluded from stage timing; cross-server verification included in throughput. Latency percentiles include successful streaming turns only.

| Clients | Admitted | Completed/attempted | Turns/s | First text p95 (s) | Completion p95 (s) | Errors |
|---:|---:|---:|---:|---:|---:|---|
| 8 | 8 | 24/24 | 1.503 | 0.9818 | 6.2453 | - |
| 32 | 32 | 96/96 | 5.3 | 1.5539 | 6.8163 | - |
| 64 | 64 | 192/192 | 5.277 | 7.176 | 12.4381 | - |

Database audit: `{"games": 104, "receipt_statuses": {"completed": 312}, "simulated_llm_calls": 520}`

Worker resource samples: `{"peak_worker_rss_mb": 139.75, "worker_cpu_seconds": 8.312}`

These local results do not establish production capacity. The client, app and database share this machine; the WSGI server is Waitress, not production Gunicorn. Capacity mode raises rate-limit budgets only in the isolated harness. Guardrails mode keeps normal limits and all clients share one IP.
