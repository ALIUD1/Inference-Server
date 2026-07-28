from redis.asyncio import Redis
import uuid
import asyncio

r = Redis(host = 'localhost', port = 6379, db = 0)
#frontend commands
def add_to_queue(job_id, image_bytes):
    r.set(job_id, image_bytes)
    r.rpush("jobs", job_id)

async def response_reader():
    while True:
       _, response = await r.blpop("response")
        id, val = struct.unpack("<16sq",response)
        try:  
            awake_coroutine(id, val)
        except Exception as e:
            print(f"Exception in response reader" {e})

async def store_coroutine(job_id, image_bytes):
    future = asyncio.get_running_loop().create_future()
    pending_jobs[job_id] = future
    add_to_queue(job_id, image_bytes)
    return await future

async def awake_coroutine(job_id, response):
    try:
        future = pending_jobs.pop(job_id)
        future.set_result(value)
    except Exception as e:
        print(f"Exption in awake_coroutine: {e}")


#worker commands
def pop_from_queue():
    while True:
        payload = r.blpop("jobs", timeout = 1)[1]
        if payload is None:
            continue
        job_id = payload[1]
        image_bytes = r.get(job_id)
        r.delete(job_id)
        
    return (job_id, image_bytes)

def push_response_to_queue(id, val):
    paylaod = struct.pack("<16sq", id, val)
    r.rpush("response", paylaod)

if __name__ == "__main__":
    print(r.ping())
    add_to_queue(b"hello world")
