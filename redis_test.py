import redis
import uuid
import asyncio

r = redis.Redis(host = 'localhost', port = 6379, db = 0)

def add_to_queue(image_bytes):
    job_id = uuid.uuid4()
    job_id = job_id.bytes()
    r.set(job_id, image_bytes)
    r.rpush("jobs", job_id)
    return id

def response_reader():
    while True:
        response = await r.blpop("response")
        id, val = struct.unpack("<16sq",response)
        try:  
            awake_coroutine(id, val)
        except Exception as e:
            print(f"Exception in response reader" {e})

def store_coroutine(job_id):
    future - asyncio.get_running_loop().create_future()
    pending_jobs[job_id] = future
    result = await future

def awake_coroutine(job_id, response):
    try:
        future = pending_jobs.pop(job_id)
        future.set_result(value)
    except Exception as e:
        print(f"Exption in awake_coroutine: {e}")


if __name__ == "__main__":
    print(r.ping())
    add_to_queue(b"hello world")
