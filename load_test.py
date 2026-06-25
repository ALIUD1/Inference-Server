import httpx
import asyncio
#import datetime
import time

with open("pgiff.webp", "rb") as f:
    img = f.read()
files = {'file': ("pgiff.webp",img, "img/webp")}
url = "http://127.0.0.1:8001/"

async def concurrent(url, file,client):
    start = time.perf_counter()
    response = await client.post(url,files = files)
    end = time.perf_counter()
    return (start,end, response.status_code)

async def test_latency():
    async with httpx.AsyncClient() as client:
        calls = [concurrent(url,img,client) for i in range(5)]

        results = await asyncio.gather(*calls, return_exceptions = False)
        return calculate_latency(results)

def calculate_latency(results):
    total_time = 0
    count =0
    failed = []
    for result in results:
        if result[2] == 200:
            total_time += result[1] - result[0]
            count += 1
        else:
            failed.append(result)
    return [total_time/count, failed]

if __name__ == "__main__":
    print(f"Average latency was measured at: {asyncio.run(test_latency())}")