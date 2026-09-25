# Local load test

UTC: 2026-09-25T01:51:07.853054+00:00

Profile: capacity; model: simulated; servers: 2; threads/server: 16; simulated generation: 0.5 s.

Real HTTP + PostgreSQL. Closed-loop clients, no think time. Setup excluded from stage timing; cross-server verification included in throughput. Latency percentiles include successful streaming turns only.

| Clients | Admitted | Completed/attempted | Turns/s | First text p95 (s) | Completion p95 (s) | Errors |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 1 | 2/2 | 0.59 | 0.2033 | 1.595 | - |

Database audit: `{"games": 1, "receipt_statuses": {"completed": 2}, "simulated_llm_calls": 3}`

Worker resource samples: `{"peak_worker_rss_mb": 126.86, "worker_cpu_seconds": 0.156}`

These local results do not establish production capacity. The client, app and database share this machine; the WSGI server is Waitress, not production Gunicorn. Capacity mode raises rate-limit budgets only in the isolated harness. Guardrails mode keeps normal limits and all clients share one IP.
