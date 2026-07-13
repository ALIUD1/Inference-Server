import httpx
import asyncio
#import datetime
import time
import numpy as np

with open("pgiff.webp", "rb") as f:
    img = f.read()
files = {'file': ("pgiff.webp",img, "img/webp")}
url = "http://127.0.0.1:8001/"

async def concurrent(url, file,client):
    start = time.perf_counter()
    response = await client.post(url,files = file)
    end = time.perf_counter()
    return (start,end, response.status_code)

async def test_latency(connections,client):
    calls = [concurrent(url,files,client) for i in range(connections)]

    results = await asyncio.gather(*calls, return_exceptions = True)
    latency_data = calculate_latency(results)
    #print(f"{latency_data} \n")
    look_bttr(latency_data,connections)

def calculate_latency(results):
    failed = []
    exceptions = []
    data = []
    for result in results:
        if isinstance(result, Exception):
            exceptions.append(result)
        else:
            if result[2] == 200:
                time_taken = result[1] - result[0]
                data.append(time_taken)
            else:
                failed.append(result)
    #print(f"data len: {len(data)}, num failed: {len(failed)}, num exceptions{len(exceptions)}")
    if len(data) > 0:
        p25 = np.percentile(data,25)
        p50 = np.percentile(data,50)
        p75 = np.percentile(data,75)
        p95 = np.percentile(data,95)
    else:
        p25 = p50 = p75 = p95 = -1

    return [p25,p50,p75,p95, failed, exceptions]

def look_bttr(lst: "[p25,p50,p75,p90,failed, exceptions]", connections):
    print(f"""At {connections} connectsions the latency at \n 
    p25 = {lst[0]} \n
    p50 = {lst[1]} \n
    p75 = {lst[2]} \n
    p95 = {lst[3]} \n
    failures: {lst[4]}\n
    exceptions: {lst[5]}\n """)

async def warmup_requests(connections,client):
    calls = [concurrent(url,files,client) for i in range(connections)]

    results = await asyncio.gather(*calls, return_exceptions = True)
    print(f"Warmup finished running {connections} connections")

async def run_latency_test(tests):
    limits = httpx.Limits(
        max_connections = 1000,
    )
    async with httpx.AsyncClient(limits = limits) as client:
        await warmup_requests(5,client)
        for num_connections in tests:
            await test_latency(num_connections,client)
if __name__ == "__main__":
    asyncio.run(run_latency_test([10,100,200,300,500,700, 900, 1000,1200]))