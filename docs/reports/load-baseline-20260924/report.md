# Local load test

UTC: 2026-09-25T01:52:08.031190+00:00

Profile: capacity; model: simulated; servers: 2; threads/server: 16; simulated generation: 0.5 s.

Real HTTP + PostgreSQL. Closed-loop clients, no think time. Setup excluded from stage timing; cross-server verification included in throughput. Latency percentiles include successful streaming turns only.

| Clients | Admitted | Completed/attempted | Turns/s | First text p95 (s) | Completion p95 (s) | Errors |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 1 | 4/4 | 0.602 | 0.2627 | 1.66 | - |
| 8 | 8 | 32/32 | 4.537 | 0.3224 | 1.7074 | - |
| 16 | 16 | 64/64 | 8.232 | 0.4904 | 1.8782 | - |
| 32 | 32 | 128/128 | 13.689 | 0.8424 | 2.2601 | - |
| 64 | 64 | 256/256 | 14.183 | 2.8054 | 4.2158 | - |

Database audit: `{"games": 121, "receipt_statuses": {"completed": 484}, "simulated_llm_calls": 847}`

Worker resource samples: `{"peak_worker_rss_mb": 145.25, "worker_cpu_seconds": 11.484}`

These local results do not establish production capacity. The client, app and database share this machine; the WSGI server is Waitress, not production Gunicorn. Capacity mode raises rate-limit budgets only in the isolated harness. Guardrails mode keeps normal limits and all clients share one IP.
