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

@asynccontextmanager
async def lifespan(app: FastAPI):
    reader = asyncio.create_task(response_reader())
    yield


if __name__ == "__main__":
    print(r.ping())
    add_to_queue(b"hello world")
