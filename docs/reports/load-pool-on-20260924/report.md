# Local load test

UTC: 2026-09-25T02:58:37.266716+00:00

Profile: capacity; model: simulated; servers: 2; threads/server: 16; simulated generation: 0.5 s.

Short-operation PostgreSQL pool size per server: 4.

Real HTTP + PostgreSQL. Closed-loop clients, no think time. Setup excluded from stage timing; cross-server verification included in throughput. Latency percentiles include successful streaming turns only.

| Clients | Admitted | Completed/attempted | Turns/s | First text p95 (s) | Completion p95 (s) | Errors |
|---:|---:|---:|---:|---:|---:|---|
| 32 | 32 | 128/128 | 22.09 | 1.0926 | 1.6237 | - |
| 64 | 64 | 256/256 | 23.385 | 2.0252 | 2.5154 | - |

## Server timing (stream requests only)

Seconds per request, p95; nested spans overlap and must not be added. WSGI duration excludes the HTTP server queue before invocation.

| Clients | Records | WSGI | PG connect | PG pool wait | PG session lock | PG read | PG write | LLM chat | Outside WSGI |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 32 | 128 | 1.5991 | 0.4206 | 0.0513 | 0.0014 | 0.0084 | 0.0157 | 1.0443 | 0.0664 |
| 64 | 256 | 1.5511 | 0.3885 | 0.0277 | 0.0016 | 0.0103 | 0.0142 | 1.0819 | 1.406 |

Database audit: `{"games": 96, "receipt_statuses": {"completed": 384}, "simulated_llm_calls": 672}`

Worker resource samples: `{"peak_worker_rss_mb": 146.11, "worker_cpu_seconds": 10.188}`

These local results do not establish production capacity. The client, app and database share this machine; the WSGI server is Waitress, not production Gunicorn. Capacity mode raises rate-limit budgets only in the isolated harness. Guardrails mode keeps normal limits and all clients share one IP.
