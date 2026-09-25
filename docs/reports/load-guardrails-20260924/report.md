# Local load test

UTC: 2026-09-25T01:58:54.988355+00:00

Profile: guardrails; model: simulated; servers: 2; threads/server: 16; simulated generation: 0.5 s.

Real HTTP + PostgreSQL. Closed-loop clients, no think time. Setup excluded from stage timing; cross-server verification included in throughput. Latency percentiles include successful streaming turns only.

| Clients | Admitted | Completed/attempted | Turns/s | First text p95 (s) | Completion p95 (s) | Errors |
|---:|---:|---:|---:|---:|---:|---|
| 8 | 6 | 14/20 | 4.052 | 0.3229 | 1.2453 | {'http_429': 6} |

Database audit: `{"games": 6, "receipt_statuses": {"completed": 14}, "simulated_llm_calls": 22}`

Worker resource samples: `{"peak_worker_rss_mb": 130.12, "worker_cpu_seconds": 0.703}`

These local results do not establish production capacity. The client, app and database share this machine; the WSGI server is Waitress, not production Gunicorn. Capacity mode raises rate-limit budgets only in the isolated harness. Guardrails mode keeps normal limits and all clients share one IP.
