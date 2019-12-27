import json

import redis


class RedisTool(object):
    def __init__(self):

        pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True)
        self.r = redis.Redis(connection_pool=pool)

    def string_set(self, name, value):
        self.r.set(name, value)

    def string_get(self, name):
        return self.r.get(name)

    def hash_set(self, name, key, value, ):
        self.r.hset(name, key, json.dumps(value))

    def hash_get(self, name, key):
        res = self.r.hget(name, key)
        if not res:
            return None
        return json.loads(res)

    def hash_del(self, name, key):
        res = self.r.hdel(name, key)
        return res


r = RedisTool()

# s = r.hash_get('vice_auth', 17)
# print(s)