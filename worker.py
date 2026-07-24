import redis
import struct
import uuid

r = redis.Redis(host = 'localhost', port = 6379, db = 0)

def pop_from_queue():
    job_id = r.blpop("jobs", timeout = 1)[1]
    image_bytes = r.get(job_id)
    r.delete(job_id)
    return (job_id, image_bytes)

def push_response_to_queue(id, val):
    paylaod = struct.pack("<16sq", id, val)
    r.rpush("response", paylaod)
