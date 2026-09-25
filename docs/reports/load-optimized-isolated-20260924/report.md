# Local load test

UTC: 2026-09-25T01:57:12.366866+00:00

Profile: capacity; model: simulated; servers: 2; threads/server: 16; simulated generation: 0.5 s.

Real HTTP + PostgreSQL. Closed-loop clients, no think time. Setup excluded from stage timing; cross-server verification included in throughput. Latency percentiles include successful streaming turns only.

| Clients | Admitted | Completed/attempted | Turns/s | First text p95 (s) | Completion p95 (s) | Errors |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 1 | 4/4 | 0.99 | 0.2058 | 1.0993 | - |
| 8 | 8 | 32/32 | 7.084 | 0.3403 | 1.1865 | - |
| 16 | 16 | 64/64 | 12.137 | 0.4708 | 1.358 | - |
| 32 | 32 | 128/128 | 17.701 | 0.9641 | 1.8493 | - |
| 64 | 64 | 256/256 | 14.915 | 2.6464 | 3.593 | - |

Database audit: `{"games": 121, "receipt_statuses": {"completed": 484}, "simulated_llm_calls": 847}`

Worker resource samples: `{"peak_worker_rss_mb": 145.04, "worker_cpu_seconds": 13.719}`

These local results do not establish production capacity. The client, app and database share this machine; the WSGI server is Waitress, not production Gunicorn. Capacity mode raises rate-limit budgets only in the isolated harness. Guardrails mode keeps normal limits and all clients share one IP.
