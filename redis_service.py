import redis

class RedisService():
    def __init__(self,values:dict):
        self.client = redis.Redis(
            host=values.get("REDIS_HOST"),
            port=values.get("REDIS_PORT"),
            username=values.get("REDIS_USERNAME"),
            password=values.get("REDIS_PASSWORD")
        )
        print(self.client.hget('jobs:8r989389'))