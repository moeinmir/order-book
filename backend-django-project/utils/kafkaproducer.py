from confluent_kafka import Producer
from django.conf import settings
import json
import logging
import json
logger = logging.getLogger(__file__)

def send_to_kafka(topic, data):
    producer = Producer(settings.KAFKA_CONFIG)
    def delivery_report(err, msg):
        if err:
            logger.error(f'Message delivery failed: {err}')
        else:
            logger.info(f'Message delivered to {msg.topic()} [{msg.partition()}]')
    producer.produce(
        topic,
        json.dumps(data).encode('utf-8'),
        callback=delivery_report
    )
    producer.flush()

