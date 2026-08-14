"""from redis.asyncio import Redis
r = Redis(host='localhost', port=6379, db=0)
print(r.connection_pool.max_connections)"""
import redis
r = redis.Redis()
for i in range(1, 6):
    v = r.lindex("response", i)
    print(i, len(v), v[:24])