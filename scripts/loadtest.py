"""Simulate a full class against a running server: N students in teams of 3, each polling every 3 s,
playing all rounds while an admin starts/closes rounds. Prints latency stats.
Usage: python scripts/loadtest.py http://localhost:8000 <admin_password> [students=40] [pin=EUM2026]"""
import asyncio, random, statistics, sys, time
import httpx

URL, ADMIN_PW = sys.argv[1].rstrip("/"), sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 40
PIN = sys.argv[4] if len(sys.argv) > 4 else "EUM2026"
lat, errs = [], []
ROLES = ["planner", "logistics", "finance"]
SKUS = ["tee", "dress", "coat", "viral"]

async def call(c, method, path, tok=None, **kw):
    t0 = time.perf_counter()
    r = await c.request(method, URL + path, headers={"Authorization": f"Bearer {tok}"} if tok else None, **kw)
    lat.append((time.perf_counter() - t0) * 1000)
    if r.status_code >= 500: errs.append((path, r.status_code))
    return r

async def student(i, stop):
    team, role = f"Team{i // 3 + 1:02d}", ROLES[i % 3]
    async with httpx.AsyncClient(timeout=20) as c:
        r = await call(c, "POST", "/api/join", json={"name": f"S{i}", "pin": PIN, "team": team, "roles": [role]})
        tok = r.json()["token"]; done = set()
        await asyncio.sleep(random.random() * 3)
        while not stop.is_set():
            st = (await call(c, "GET", "/api/state", tok)).json()
            g = st["game"]
            if g["phase"] == "open" and g["round"] not in done:
                await asyncio.sleep(random.uniform(0.5, 4))        # "thinking"
                if role == "planner":
                    await call(c, "POST", "/api/proposal", tok, json={"qty": {s: random.randint(20, 150) for s in SKUS}})
                elif role == "logistics":
                    await asyncio.sleep(2)
                    await call(c, "POST", "/api/modes", tok, json={"modes": {s: random.choice(["sea", "nearshore", "air"]) for s in SKUS}})
                else:
                    await asyncio.sleep(4)
                    await call(c, "POST", "/api/approve", tok, json={"approve": True})
                done.add(g["round"])
            await asyncio.sleep(3 + random.random() * 0.5)

async def main():
    stop = asyncio.Event()
    async with httpx.AsyncClient(timeout=30) as c:
        tok = (await call(c, "POST", "/api/admin/login", json={"password": ADMIN_PW})).json()["token"]
        await call(c, "POST", "/api/admin/reset", tok, json={})
        tasks = [asyncio.create_task(student(i, stop)) for i in range(N)]
        await asyncio.sleep(8)
        for rnd in range(6):
            await call(c, "POST", "/api/admin/start", tok)
            await asyncio.sleep(14)
            await call(c, "POST", "/api/admin/close", tok)
            await asyncio.sleep(3)
        s = (await call(c, "GET", "/api/state", tok)).json()
        stop.set(); await asyncio.gather(*tasks, return_exceptions=True)
    lat.sort()
    print(f"{N} students, {len(lat)} requests | median {statistics.median(lat):.0f} ms | p95 {lat[int(len(lat)*.95)]:.0f} ms | max {lat[-1]:.0f} ms | 5xx errors: {len(errs)}")
    print("final phase:", s["game"]["phase"], "| teams:", len(s["admin"]["teams"]), "| approved last round:", sum(t["approved"] for t in s["admin"]["teams"]))

asyncio.run(main())
