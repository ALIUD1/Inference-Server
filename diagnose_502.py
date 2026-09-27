"""Reproduce load_test.py's exact shape (one shared client, all levels back to
back) and capture full detail plus a timestamp for every non-200 / exception."""
import asyncio
import collections
import time

import httpx

URL = "http://127.0.0.1:8001/"
LEVELS = [10, 100, 200, 300, 500, 700, 900, 1000, 1200]

with open("pgiff.webp", "rb") as f:
    IMG = f.read()

T0 = time.perf_counter()
BAD = []


async def one(client):
    files = {'file': ("pgiff.webp", IMG, "img/webp")}
    try:
        r = await client.post(URL, files=files)
        if r.status_code != 200:
            BAD.append((time.perf_counter() - T0, "status", r))
        return r.status_code
    except Exception as e:
        BAD.append((time.perf_counter() - T0, "exception", e))
        return type(e).__name__


async def level(client, n, label):
    start = time.perf_counter()
    out = await asyncio.gather(*[one(client) for _ in range(n)])
    wall = time.perf_counter() - start
    counts = collections.Counter(out)
    ok = counts.get(200, 0)
    other = {k: v for k, v in counts.items() if k != 200}
    print(f"[t={start - T0:7.1f}s] {label:>10}  n={n:<5} wall={wall:6.2f}s  "
          f"ok={ok:<5} thru={ok / wall:6.1f}/s  other={other or 'none'}")


async def main():
    limits = httpx.Limits(max_connections=1000)
    timeout = httpx.Timeout(60.0)
    async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
        await level(client, 40, "warmup")
        for n in LEVELS:
            await level(client, n, "level")

    print(f"\n=== {len(BAD)} failures total ===")
    if not BAD:
        print("none")
        return

    kinds = collections.Counter(
        r.status_code if k == "status" else type(r).__name__ for _, k, r in BAD)
    print("breakdown   :", dict(kinds))
    times = [t for t, _, _ in BAD]
    print(f"time window : {min(times):.1f}s .. {max(times):.1f}s of {time.perf_counter() - T0:.1f}s total")

    print("\n=== first 3 non-200 responses in full ===")
    shown = 0
    for t, kind, r in BAD:
        if kind != "status" or shown >= 3:
            continue
        shown += 1
        print("-" * 60)
        print(f"t={t:.1f}s  status={r.status_code} {r.reason_phrase}  http={r.http_version}")
        for k, v in r.headers.items():
            print(f"    {k}: {v}")
        print("body:", repr(r.text[:400]) if r.text else "<empty>")


asyncio.run(main())
