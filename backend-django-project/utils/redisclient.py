import redis
from django.conf import settings
import logging

logger = logging.getLogger(__file__)

redis_config = settings.REDIS_CONFIG

redis_client = redis.Redis(
    host=redis_config['host'],
    port=redis_config['port'],
    db=redis_config['db'],  # Database number (0-15)
    decode_responses=redis_config['decode_responses'], 
    password=redis_config['password']
)


class RedisClient:
    redis_client = redis_client

    @staticmethod
    def set_item(key,value):

        result = redis_client.set(str(key),value)
        logger.info('result %s',result)
        return result

    @staticmethod
    def get_item(key):

        result = redis_client.get(str(key))
        logger.info('result %s',result)
        return result


