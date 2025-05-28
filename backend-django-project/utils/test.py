from django.test import TestCase
from .kafkaconsumer import kafka_consumer

@kafka_consumer(topic="1")
def test_consumer_wrapper(message, *args, **kwargs):
    print("message is here")
    print(message)



class ProductTestCase(TestCase):
    test_consumer_wrapper()
