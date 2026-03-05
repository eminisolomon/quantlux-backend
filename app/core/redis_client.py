import redis.asyncio as redis
from app.core.settings import settings
from app.utils.logger import logger


class RedisClient:
    _instance = None
    _redis = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def redis(self) -> redis.Redis:
        if self._redis is None:
            self.connect()
        return self._redis

    def connect(self):
        logger.info(f"Connecting to Redis at {settings.REDIS_URL}")
        self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def disconnect(self):
        if self._redis:
            await self._redis.aclose()
            self._redis = None


redis_client = RedisClient()
