# Local load test

UTC: 2026-09-25T02:58:15.069136+00:00

Profile: capacity; model: simulated; servers: 2; threads/server: 16; simulated generation: 0.5 s.

Short-operation PostgreSQL pool size per server: 0.

Real HTTP + PostgreSQL. Closed-loop clients, no think time. Setup excluded from stage timing; cross-server verification included in throughput. Latency percentiles include successful streaming turns only.

| Clients | Admitted | Completed/attempted | Turns/s | First text p95 (s) | Completion p95 (s) | Errors |
|---:|---:|---:|---:|---:|---:|---|
| 32 | 32 | 128/128 | 19.696 | 1.1408 | 1.6509 | - |
| 64 | 64 | 256/256 | 21.474 | 2.3696 | 2.8911 | - |

## Server timing (stream requests only)

Seconds per request, p95; nested spans overlap and must not be added. WSGI duration excludes the HTTP server queue before invocation.

| Clients | Records | WSGI | PG connect | PG pool wait | PG session lock | PG read | PG write | LLM chat | Outside WSGI |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 32 | 128 | 1.6465 | 0.5586 | 0 | 0.001 | 0.0067 | 0.0166 | 1.0873 | 0.0546 |
| 64 | 256 | 1.6521 | 0.6028 | 0 | 0.0011 | 0.0075 | 0.0196 | 1.0719 | 1.7044 |

Database audit: `{"games": 96, "receipt_statuses": {"completed": 384}, "simulated_llm_calls": 672}`

Worker resource samples: `{"peak_worker_rss_mb": 144.38, "worker_cpu_seconds": 8.953}`

These local results do not establish production capacity. The client, app and database share this machine; the WSGI server is Waitress, not production Gunicorn. Capacity mode raises rate-limit budgets only in the isolated harness. Guardrails mode keeps normal limits and all clients share one IP.
