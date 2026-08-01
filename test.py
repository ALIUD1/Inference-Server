from redis.asyncio import Redis
r = Redis(host='localhost', port=6379, db=0)
print(r.connection_pool.max_connections)