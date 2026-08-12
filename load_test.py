import httpx
import asyncio
#import datetime
import time
import numpy as np
import redis

r = redis.Redis(host='localhost', port=6379, db=0)

# Flush current database
r.flushdb()

with open("pgiff.webp", "rb") as f:
    img = f.read()
files = {'file': ("pgiff.webp",img, "img/webp")}
url = "http://127.0.0.1:8001/"

async def concurrent(url, file,client):
    #print("now in concurrent")
    client_start = time.perf_counter()
    response = await client.post(url,files = file)
    client_end = time.perf_counter()
    if response.status_code != 200:
        return (client_start,client_end, response.status_code,-1,response.headers.get("server"), response.text)
    return (client_start,client_end, response.status_code,response.json()["Server_Rate"])

async def test_latency(connections,client):
    #print("im in teest_latency")
    calls = [concurrent(url,files,client) for i in range(connections)]
    wall_start_time = time.perf_counter()
    results = await asyncio.gather(*calls, return_exceptions = True)
    wall_end_time = time.perf_counter()
    latency_data = calculate_latency(results,wall_end_time - wall_start_time)
    #print(f"{latency_data} \n")
    look_bttr(latency_data,connections)

def calculate_latency(results, wall_time):
    #print("Now in calculate latency")
    """
    results is a list with the following data
    0: Client Start time
    1: Client End time
    2: Response Status Code
    4: Server time
    5: Wall Time
    """
    failed = {}
    exceptions = []
    client_time_data = []
    server_time_data = []
    sucessful = 0
    for result in results:
        if isinstance(result, Exception):
            exceptions.append(result)
        else:
            if result[2] == 200:
                sucessful += 1
                time_taken = result[1] - result[0]
                client_time_data.append(time_taken)
                server_time_data.append(result[3])
            else:
                if result[2] not in failed:
                    failed[result[2]] = [1, result[4], result[5]]
                else:
                    failed[result[2]][0] += 1
    #print(f"data len: {len(data)}, num failed: {len(failed)}, num exceptions{len(exceptions)}")
    client_time_percentiles = {}
    server_time_percentiles = {}
    if len(server_time_data) > 0 and len(client_time_data) > 0:
        for percent in [25,50,75,95]:
            server_time_percentiles[f"p{percent}"] = np.percentile(server_time_data, percent)
            client_time_percentiles[f"p{percent}"] = np.percentile(client_time_data, percent)
    else:
        for percent in [25,50,75,95]:
            server_time_percentiles[f"p{percent}"] = -1
            client_time_percentiles[f"p{percent}"] = -1
    throughput = sucessful / wall_time
    return [client_time_percentiles, failed, exceptions, server_time_percentiles, wall_time, sucessful, throughput]

def look_bttr(latency_data, connections):
    #print("now in look better")
    print(f"At {connections} connectsions the latency at \n")
    for (client_key,client_value) , (server_key, server_value) in zip(latency_data[0].items(), latency_data[3].items()):
        print(f"Client_time: {client_key} = {client_value} \t Server_time: {server_key} = {server_value} \t Time Difference = {client_value - server_value}")
    print(f"Wall time: {latency_data[4]} \t Sucessful requests: {latency_data[5]} \t Throughput: {latency_data[6]}")
    print(f"failures: {latency_data[1]}\n")
    print(f"exceptions: {latency_data[2]}\n")

async def warmup_requests(connections,client):
    calls = [concurrent(url,files,client) for i in range(connections)]

    results = await asyncio.gather(*calls, return_exceptions = True)
    print(f"Warmup finished running {connections} connections")

async def run_latency_test(tests):
    limits = httpx.Limits(
        max_connections = 1500,
    )
    async with httpx.AsyncClient(limits = limits, timeout = httpx.Timeout(5.0, read =30.0)) as client:
        await warmup_requests(40,client)
        for num_connections in tests:
            await test_latency(num_connections,client)
if __name__ == "__main__":
    asyncio.run(run_latency_test([10,100,200,300,500,700, 900, 1000,1200]))