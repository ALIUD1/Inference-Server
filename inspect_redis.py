import redis
import os

r = redis.Redis(host='localhost', port=6379, db=0, password=os.environ["REDIS_PASSWORD"])

print("jobs      :", r.llen("jobs"))
print("response  :", r.llen("response"))

keys = r.keys("*")
payload_keys = [k for k in keys if k not in (b"jobs", b"response")]
print("payload keys:", len(payload_keys))
print("total keys  :", len(keys))
