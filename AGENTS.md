# Agent guide

Read `SPEC.md` first. It holds the architecture, the Redis and HTTP contracts, current status, open issues (stable IDs like F2, W1), and the roadmap. `README.md` is the public write up.

## Rules

1. This is a learning project. Alex writes the implementation in `main.py`, `worker.py`, and `load_test.py`. Do not write or rewrite code in those files. Give hints first, then answers if asked; ask what shape he thinks the fix is.
2. Read only diagnostic scripts (like `inspect_redis.py`, `diagnose_502.py`) and docs are fine to write.
3. Reproduce a problem before proposing a fix. Back causal claims with data, not "the last edit did it".
4. Watch process boundaries. A running process never sees file edits, new env vars, or another process's module attributes. Restart it.
5. Library facts and API defaults: just state them.
6. Prose: casual, direct, no flattery, no em dashes.
7. Never quote a benchmark number that is not backed by a committed log. See SPEC section 6.

## Collaboration

- `SPEC.md` is the shared workspace. If your change alters behavior, a contract, status, or an open issue, update `SPEC.md` in the same PR and add a line to its decisions log.
- Reference issue IDs from `SPEC.md` section 7 in commit messages and PRs.
- One branch per task, PR into `main`. Never force push `main`.
- Commits and PRs are authored as `ALIUD1`. No AI co-author trailers or "generated with" lines.
- Never commit secrets (`REDIS_PASSWORD`), LAN IPs, `CLAUDE.md`, `.claude/`, or `HANDOFF*.md`.
- Benchmarks: commit the raw log to `logs/` with a header naming worker count, hosts, threads, batch size, and fill wait.
