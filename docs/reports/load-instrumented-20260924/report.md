# Local load test

UTC: 2026-09-25T02:39:30.381330+00:00

Profile: capacity; model: simulated; servers: 2; threads/server: 16; simulated generation: 0.5 s.

Real HTTP + PostgreSQL. Closed-loop clients, no think time. Setup excluded from stage timing; cross-server verification included in throughput. Latency percentiles include successful streaming turns only.

| Clients | Admitted | Completed/attempted | Turns/s | First text p95 (s) | Completion p95 (s) | Errors |
|---:|---:|---:|---:|---:|---:|---|
| 16 | 16 | 64/64 | 11.967 | 0.524 | 1.4345 | - |
| 32 | 32 | 128/128 | 18.6 | 0.9725 | 1.8614 | - |
| 64 | 64 | 256/256 | 21.229 | 1.792 | 2.7101 | - |

## Server timing (stream requests only)

Seconds per request, p95; nested spans overlap and must not be added. WSGI duration excludes the HTTP server queue before invocation.

| Clients | Records | WSGI | PG connect | PG session lock | PG read | PG write | LLM chat | Outside WSGI |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 16 | 64 | 1.4299 | 0.3484 | 0.0009 | 0.0067 | 0.013 | 1.0256 | 0.0255 |
| 32 | 128 | 1.8585 | 0.6696 | 0.0011 | 0.0073 | 0.012 | 1.1021 | 0.0454 |
| 64 | 256 | 1.6769 | 0.5702 | 0.0013 | 0.0093 | 0.0121 | 1.1301 | 1.4738 |

Database audit: `{"games": 112, "receipt_statuses": {"completed": 448}, "simulated_llm_calls": 784}`

Worker resource samples: `{"peak_worker_rss_mb": 145.59, "worker_cpu_seconds": 11.375}`

These local results do not establish production capacity. The client, app and database share this machine; the WSGI server is Waitress, not production Gunicorn. Capacity mode raises rate-limit budgets only in the isolated harness. Guardrails mode keeps normal limits and all clients share one IP.
