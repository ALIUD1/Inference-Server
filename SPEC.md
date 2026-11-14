# Inference Server Spec

Living spec for this repo. The single source of truth for what the system is, what state it is in, and what comes next. `README.md` is the public story; this file is the working contract. Any agent or person who changes behavior updates this file in the same PR.

Last updated: 2026-11-14

## 1. Goal

Serve ResNet-18 image classification over HTTP with a frontend that never blocks on inference, workers that batch, and workers that can live on other machines. Measure it honestly under load (target: 1,200 concurrent requests). It is a learning project, so understanding beats features.

## 2. Architecture

```
client --POST /--> main.py (FastAPI, 1 process, 1 event loop, :8001)
                     |  SET <job_id> <image bytes>
                     |  RPUSH jobs <job_id>
                     v
                   Redis (:6379, password, lives with the frontend)
                     |  BLPOP jobs  (fill to 8 jobs or 200 ms)
                     v
                   worker.py x N (separate processes, any machine)
                     |  MGET + DEL payloads, ResNet-18 forward on [n,3,224,224]
                     |  RPUSH response <24 byte reply>
                     v
                   main.py response_reader task: BLPOP response, resolve Future
```

Only bytes cross process boundaries. Nothing is shared in memory between the frontend and workers.

## 3. Contracts

Change any of these and every component must change in the same PR.

### HTTP

`POST /` with multipart field `file` (any image Pillow can open).

Response `200`:
```json
{"Category_Number": 652, "Server_Rate": 0.21}
```
- `Category_Number`: ImageNet class index (int), or `null` if the frontend hit an internal error (see issue F3).
- `Server_Rate`: seconds the request spent inside the handler (float).

No other status codes are produced on purpose yet. No timeout: a dropped job hangs forever (F2).

### Redis

| Key | Type | Writer | Reader | Contents |
|---|---|---|---|---|
| `<job_id>` | string | frontend `SET` | worker `MGET` then `DEL` | raw uploaded image bytes, no TTL |
| `jobs` | list | frontend `RPUSH` | workers `BLPOP` | 16 byte job ids |
| `response` | list | workers `RPUSH` | frontend reader `BLPOP` | 24 byte replies |

- `job_id` = `uuid.uuid4().bytes` (16 raw bytes, used directly as the Redis key).
- Reply = `struct.pack("<16sq", job_id, class_index)`: little endian, 16 bytes id + int64.
- Keys are not namespaced. The frontend runs `FLUSHDB` on startup and `load_test.py` runs it on import.
- Auth: every process reads the password from env var `REDIS_PASSWORD` and crashes on start if it is missing (intended).

### Timeouts invariant

redis-py 8 defaults `socket_timeout=5`. Every `BLPOP` timeout must stay strictly below that, with margin. Current values: reader 1 s, worker 1 s idle and 0.05 s during batch fill. Breaking this killed the reader task silently once (see README "Things that broke").

### Worker CLI

| Flag | Default | Meaning |
|---|---|---|
| `--redis-host` | `127.0.0.1` | Redis host, set this to run a worker on another machine |
| `--redis-port` | `6379` | Redis port |
| `--threads`, `-t` | `1` | `torch.set_num_threads` |

Hardcoded in `worker.py`: `BATCH_FILL_WAIT_TIME = 0.2`, `BATCH_SIZE = 8`. Config is read once at process start. Editing the file or setting env vars never changes a running worker; restart it.

## 4. Components

| File | Owner | Role |
|---|---|---|
| `main.py` | Alex | FastAPI app, lifespan starts `response_reader`, `pending_jobs` dict of `job_id -> Future` |
| `worker.py` | Alex | batch fill loop (`pop_from_queue`), `work` runs preprocessing + forward, `push_response_to_queue` |
| `load_test.py` | Alex | sweep: warmup 40, then 10..1200 concurrent on one httpx client, p25..p95, throughput, failures by status |
| `single_request.py` | any | one POST with timing, sanity check |
| `inspect_redis.py` | any | read only: queue lengths and payload key count |
| `diagnose_502.py` | any | sweep that records full headers for every failure |
| `logs/` | any | raw benchmark output cited in README |

Owner "Alex" means agents do not write implementation code in that file. See `AGENTS.md`.

## 5. Running it

See `README.md` "Run it". Order: Redis, frontend (`uvicorn main:app --port 8001`), N workers, `single_request.py`, `load_test.py`. Python 3.14, deps pinned in `requirements.txt`.

Dev setup today: Windows laptop runs Redis (Docker) and the frontend; workers run there and on a Mac over the LAN (inbound TCP 6379 allowed on the private network only). The Windows box also runs Postgres on :8000, so the frontend uses :8001.

## 6. Status

| Step | What | Status |
|---|---|---|
| 0-3 | Endpoint, load tester, multiple workers | done |
| 4 | Redis queue, reader task, one torch thread per worker | done |
| 5 | Worker side batching (8 jobs or 200 ms) | in code; speedup **not yet measured under control** |
| 5b | Workers on other machines (`--redis-host`, Redis password) | in progress: Mac reaches Redis; more flags pending |
| 6 | Bounded failure (timeouts, bad input, backpressure) | not started |
| 7 | Heartbeats, failover, requeue of in flight jobs | not started |
| 8 | Docker, final benchmark vs step 1 | not started |

Model versioning (v1/v2 side by side) was cut.

### Numbers we trust

Only the 4 worker, 1 thread, unbatched table in `README.md` (from `logs/step4_4_workers.txt`): flat at about 31 req/s from 100 concurrent up. Any batching speedup figure (for example "1.6x") is **unverified**: machine speed swung about 2x between days, and worker count was never confirmed during the batched run. Do not quote one until the controlled rerun in section 8 is committed.

## 7. Open issues

IDs are stable; reference them in commits and PRs. Remove a row only in the PR that fixes it.

### Frontend (`main.py`)
- **F1** `main.py:20` loads ResNet-18 and `preprocess` at import, but the frontend never runs inference. Costs startup time and memory.
- **F2** `main.py:51` `await future` has no timeout. A job a worker drops hangs its request forever. Wants a 504.
- **F3** `main.py:46-54` `store_coroutine` catches every exception and returns `None`, so the client gets `200` with `Category_Number: null`.
- **F4** `main.py:40` `struct.unpack` sits outside the `try`. One malformed reply kills the reader (now visible via `on_done`, but still fatal).
- **F5** One shared `response` list means one frontend process. A second uvicorn worker would steal replies. Fix shape: per process reply list.
- **F6** `main.py:27` pool `max_connections=1000` grows during bursts and never shrinks.
- **F7** `main.py:91` `FLUSHDB` on startup also wipes jobs that remote workers are about to read.
- **F8** No upload size limit or content check before queueing.

### Worker (`worker.py`)
- **W1** `worker.py:65-79` an image that fails preprocessing is skipped with no reply, so that request hangs (ties to F2). If every image fails, `torch.stack([])` raises and the whole batch is dropped.
- **W2** `worker.py:53-54` payloads are deleted before inference. A worker crash mid batch loses those jobs with no requeue.
- **W3** `worker.py:18-19` batch size and fill wait are constants, not flags. A sweep needs fresh processes per value anyway.
- **W4** Startup prints do not include hostname, so logs from multi machine runs cannot be attributed.
- **W5** `worker.py:51` `batch = []` is dead code.

### Load test (`load_test.py`)
- **L1** `load_test.py:105` the sweep runs inside a nine iteration loop over unused values, left over from the broken batch fill sweep.
- **L2** `load_test.py:12` `FLUSHDB` at import races with running workers.
- **L3** Exceptions are collected into an unbounded list. Aggregate by `type(e).__name__` like failures.
- **L4** No record of worker count, hosts, or config in the output, so a log cannot prove what it measured.

### Ops
- **O1** 502s above 700 concurrent are not root caused. They carried no `server` header (uvicorn always sends one), which pointed at a local HTTP proxy on the dev machine. Turn every proxy off, including TUN mode, before benchmarking.
- **O2** Payload keys have no TTL (ties to W1, W2).
- **O3** Back to back 1,200 bursts leave sockets in TIME_WAIT; space runs out and the next run sees `ConnectTimeout`.

## 8. Roadmap (in order)

1. Worker flags: `--wait`, `--batch-size`, `--no-op` (skip the model, return a fixed class, measures the plumbing ceiling), startup line with hostname and config (W3, W4).
2. Launcher that kills old workers and starts N fresh ones, then confirms all N printed their config. Guards against stale processes running old code.
3. Fix the harness (L1, L2, L3, L4): output starts with a config header listing worker count, hosts, threads, batch size, wait.
4. Controlled rerun, interleaved: no-op ceiling, 4x1 and 4x2 workers, batch 1 vs 8, 3 repeats each, laptop on AC and awake, proxies off. Commit raw logs. Only then put a batching number in README.
5. Bounded failure: 504 on timeout (F2), 422 on unreadable image (W1, F8), 503 when `jobs` is too deep, real errors instead of `null` (F3).
6. Heartbeats and failover: workers report liveness, in flight jobs get requeued (W2, O2).
7. Dockerfile and final benchmark vs step 1.

## 9. Decisions log

Append, newest first. One line each: date, decision, why.

- 2026-11-14: Added `SPEC.md` and `AGENTS.md` as the shared workspace for agents. `CLAUDE.md` and `HANDOFF*.md` stay private and gitignored.
- 2026-10-08: History rewritten to drop private notes and `__pycache__`; README written; requirements pinned.
- 2026-10-06: Redis password via `REDIS_PASSWORD`; workers take `--redis-host`; removed `import worker` from the load test (it changed config in the wrong process).
- 2026-09: Model versioning cut from scope.
- 2026-08: `BLPOP` with fractional timeout instead of polling `LPOP` for batch fill; one `MGET` + one `DEL` per batch.
- 2026-08: Reader `BLPOP` timeout 1 s and a done callback on the reader task (redis-py 8 `socket_timeout=5`).
- 2026-08: `torch.set_num_threads(1)` per worker; default threads made workers fight over cores.
- 2026-07: Separate frontend and workers through Redis lists; only bytes cross processes.
