from utils.logwrraper import *
from utils.kafkaproducer import *
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from .order_service import OrderService
from utils.logwrraper import log_variables_and_return
from ..models import Order
from utils.redisclient import RedisClient
from utils.kafkaconsumer import kafka_consumer
from  confluent_kafka import Consumer
import json
class ScheduleExecuteMatchedOrders():

    @classmethod
    @log_variables_and_return
    def initialize(cls):
        cls.token_pairs = OrderService.get_token_pairs()
        logger.info("token pairs are here")

    @classmethod
    @log_variables_and_return
    def execute_batch(cls,execution_batch):
        logger.info(f"executing batch:{execution_batch}")
        
        for batch in execution_batch:
            sell_order_id = batch['sell_order_id']
            buy_order_id = batch['buy_order_id']
            pair_amount = batch['pair_amount']
            base_amount = batch['base_amount']
            logger.info(f"executing batch sell order:{sell_order_id}")
            logger.info(f"executing batch buy order:{buy_order_id}")
            logger.info(f"executing batch pair amount:{pair_amount}")
            logger.info(f"executing batch base amount:{base_amount}")   
            cls.execute_order_pair(sell_order_id,buy_order_id,pair_amount,base_amount)
          
    @log_variables_and_return
    def execute_order_pair(sell_order_id,buy_order_id,pair_amount,base_amount):
        logger.info("executing order pair")
        logger.info(f"sell order: {sell_order_id}")
        logger.info(f"sell order: {buy_order_id}")
        logger.info(f"sell order: {pair_amount}")
        logger.info(f"sell order: {base_amount}")
        sell_order = OrderService.get_order_by_id(sell_order_id)
        buy_order = OrderService.get_order_by_id(buy_order_id)
        sell_required_account_balance = sell_order.required_token_account_balance
        logger.info(f"sellorderrequiredaccountbalance:{sell_required_account_balance}")
        sell_other_account_balance = sell_order.other_token_account_balance
        buy_required_account_balance = buy_order.required_token_account_balance
        buy_other_account_balance = buy_order.other_token_account_balance
        for order in {sell_required_account_balance,sell_other_account_balance,buy_required_account_balance,sell_other_account_balance}:
            if not order.lock_if_not():raise Exception
        sell_required_account_balance.locked_amount = sell_required_account_balance.locked_amount - pair_amount
        sell_other_account_balance.free_amount = sell_other_account_balance.free_amount + base_amount
        buy_required_account_balance.locked_amount = buy_other_account_balance.locked_amount - base_amount
        buy_other_account_balance.free_amount = buy_other_account_balance.free_amount + pair_amount
        sell_order.remaining_amount = sell_order.remaining_amount - pair_amount
        sell_order.filled_amount = sell_order.filled_amount + pair_amount
        if (buy_order.type == Order.OrderType.LIMIT):
            buy_order.remaining_amount = buy_order.remaining_amount - pair_amount
            buy_order.filled_amount = buy_order.filled_amount + pair_amount
        else:
            buy_order.remaining_amount = buy_order.remaining_amount - base_amount
            buy_order.filled_amount = buy_order.filled_amount + base_amount
        if(sell_order.remaining_amount<0):
            logger.info(f"remaining amount:{sell_order.remaining_amount}") 
        if(buy_order.remaining_amount<0):
            logger.info(f"remaining amount:{buy_order.remaining_amount}")
        sell_order.see_if_it_is_complete_and_save()
        buy_order.see_if_it_is_complete_and_save()    
        sell_required_account_balance.unlock_and_save()
        sell_other_account_balance.unlock_and_save()
        buy_required_account_balance.unlock_and_save()
        buy_other_account_balance.unlock_and_save()
        last_price = base_amount//pair_amount
        RedisClient.set_item(sell_order.token_pair.id,last_price)


    @classmethod
    def start_batch_worker(cls, token_pair):
        topic = str(token_pair.id)
        consumer = Consumer(settings.KAFKA_CONFIG)
        consumer.subscribe([topic])
        try:
            while True:
                msg = consumer.poll(timeout=2.0)
                if msg is None:
                    continue
                if msg.error():
                    logger.error(f"Consumer error: {msg.error()}")
                    continue
                batch = cls.reverse_execution_batch_to_be_used_in_execution(msg)
                logger.info(f'batch after:{batch}')
                cls.execute_batch(batch)
        finally:
            consumer.close()



    @staticmethod
    def reverse_execution_batch_to_be_used_in_execution(message):
        batch = message.value().decode('utf-8')
        logger.info(batch)
        try:
            batch = json.loads(batch)
            logger.info(batch)
            return batch
        except:
            logger.error('error while converting')    
            raise

    @classmethod
    @log_variables_and_return
    def execute_batches_parallel(cls):
        cls.initialize()
        with ThreadPoolExecutor(max_workers=len(cls.token_pairs)) as executor:
            futures = []
            for token_pair in cls.token_pairs:
                futures.append(executor.submit(cls.start_batch_worker, token_pair))
                
