
from confluent_kafka import Consumer
from django.conf import settings
from functools import wraps
import logging
import time
logger = logging.getLogger(__file__)

def kafka_consumer(topic):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            consumer = None
            try:
                consumer = Consumer(settings.KAFKA_CONFIG)
                consumer.subscribe([topic])
                shutdown = False
                def shutdown_handler(signum, frame):
                    nonlocal shutdown
                    shutdown = True
                import signal
                signal.signal(signal.SIGTERM, shutdown_handler)
                signal.signal(signal.SIGINT, shutdown_handler)
                while not shutdown:
                    try:
                        records = consumer.poll(timeout=1) 
                        print(f"records:{records}")
                        if not records:
                            logger.info("There is no message")
                            continue
                        if records.error():
                            logger.error(f'Error in pulling{records.error()}')
                        else:
                            func(records.value(),*args,**kwargs)
                    except Exception as e:
                        logging.error(f"Error in consumer loop: {str(e)}")
                        time.sleep(5)
            finally:
                if consumer is not None:
                    consumer.close()
        return wrapper
    return decorator


