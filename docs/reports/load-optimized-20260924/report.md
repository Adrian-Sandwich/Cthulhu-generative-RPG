# Local load test

Exploratory run: the regression suite ran concurrently during part of this
measurement. Do not use it for the baseline comparison; use
`../load-optimized-isolated-20260924/report.md` instead.

UTC: 2026-09-25T01:55:33.414389+00:00

Profile: capacity; model: simulated; servers: 2; threads/server: 16; simulated generation: 0.5 s.

Real HTTP + PostgreSQL. Closed-loop clients, no think time. Setup excluded from stage timing; cross-server verification included in throughput. Latency percentiles include successful streaming turns only.

| Clients | Admitted | Completed/attempted | Turns/s | First text p95 (s) | Completion p95 (s) | Errors |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 1 | 4/4 | 0.957 | 0.352 | 1.2388 | - |
| 8 | 8 | 32/32 | 7.001 | 0.332 | 1.2081 | - |
| 16 | 16 | 64/64 | 11.9 | 0.5416 | 1.432 | - |
| 32 | 32 | 128/128 | 18.122 | 0.8982 | 1.7813 | - |
| 64 | 64 | 256/256 | 15.297 | 2.5094 | 3.3775 | - |

Database audit: `{"games": 121, "receipt_statuses": {"completed": 484}, "simulated_llm_calls": 847}`

Worker resource samples: `{"peak_worker_rss_mb": 144.67, "worker_cpu_seconds": 12.938}`

These local results do not establish production capacity. The client, app and database share this machine; the WSGI server is Waitress, not production Gunicorn. Capacity mode raises rate-limit budgets only in the isolated harness. Guardrails mode keeps normal limits and all clients share one IP.
