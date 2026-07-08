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
    response = await client.post(url,files = files)
    end = time.perf_counter()
    return (start,end, response.status_code)

async def test_latency(connections):
    limits = httpx.Limits(
        max_connections = 1000,
    )
    async with httpx.AsyncClient(limits = limits) as client:
        calls = [concurrent(url,img,client) for i in range(connections)]

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
    print(f"data len: {len(data)}, num failed: {len(failed)}, num exceptions{len(exceptions)}")
    p25 = np.percentile(data,25)
    p50 = np.percentile(data,50)
    p75 = np.percentile(data,75)
    p95 = np.percentile(data,95)
    
    return [p25,p50,p75,p95, failed, exceptions]

def look_bttr(lst: [p25,p50,p75,p90,failed, exceptions], connections):
    print(f"""At {connections} connectsions the latency at \n 
    p25 = {lst[0]} \n
    p50 = {lst[1]} \n
    p75 = {lst[2]} \n
    p95 = {lst[3]} \n
    failures: {lst[4]}\n
    exceptions: {lst[5]}\n """)

if __name__ == "__main__":
    asyncio.run(test_latency(10))
    asyncio.run(test_latency(100))