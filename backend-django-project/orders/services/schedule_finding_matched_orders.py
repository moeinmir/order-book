from utils.logwrraper import *
from utils.kafkaproducer import *
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from .order_service import OrderService
from .match_orders_service import MatchOrdersService
class ScheduleFindingMatchedOrders():
       
    token_pairs = []
    
    _lock = Lock()

    @classmethod
    @log_variables_and_return
    def initialize(cls):
        cls.token_pairs = OrderService.get_token_pairs()
        logger.info("token pairs are here")
      
    @classmethod
    @log_variables_and_return
    def find_matched_orders(cls,token_pair):
        logger.info("finding matches")
        logger.info(f"tokenpair,{token_pair}")
        while True:
            try:
                time.sleep(2)
                logger.info(f"token_pair:{token_pair}")
                execution_batch = MatchOrdersService.fill_sell_market_best_interest(token_pair.id)
                logger.info(f"execution bach:{execution_batch}")
                if execution_batch:ScheduleFindingMatchedOrders.send_execution_batch_to_kafka(execution_batch,token_pair.id)
                logger.info(f"execution bach:{execution_batch}")
            except Exception as e:
                logger.error(f"Error matching orders {token_pair}: {e}")
            try:    
                execution_batch = MatchOrdersService.fill_sell_limit_best_interest(token_pair.id)
                logger.info(f"execution bach:{execution_batch}")
                if execution_batch:ScheduleFindingMatchedOrders.send_execution_batch_to_kafka(execution_batch,token_pair.id)
            except Exception as e:
                logger.error(f"Error matching orders {token_pair}: {e}")
            try:   
                execution_batch = MatchOrdersService.fill_buy_market_best_interest(token_pair.id)
                logger.info(f"execution bach:{execution_batch}")
                if execution_batch:ScheduleFindingMatchedOrders.send_execution_batch_to_kafka(execution_batch,token_pair.id)
            except Exception as e:logger.error(f"Error matching orders {token_pair}: {e}")
            try:    
                execution_batch = MatchOrdersService.fill_buy_limit_best_interest(token_pair.id)
                logger.info(f"execution bach:{execution_batch}")
                if execution_batch:ScheduleFindingMatchedOrders.send_execution_batch_to_kafka(execution_batch,token_pair.id)
            except Exception as e:
                logger.error(f"Error matching orders {token_pair}: {e}")
            logger.info("does execution batch getting filled")
    
    @staticmethod            
    def serialize_execution_batch(execution_batch):
        result = []
        for (buy_order,sell_order),(pair_amount,base_amount) in execution_batch:
            result.append({'buy_order_id':buy_order.id,'sell_order_id':sell_order.id,'pair_amount':pair_amount,'base_amount':base_amount})
        return result

    @staticmethod
    def send_execution_batch_to_kafka(execution_batch, token_pair_id):
        result = ScheduleFindingMatchedOrders.prepare_execution_batch_to_be_send_to_kafka(execution_batch)
        send_to_kafka(topic=str(token_pair_id),data= result)

    @staticmethod
    def prepare_execution_batch_to_be_send_to_kafka(execution__batch):
        result = []
        for (buy_order,sell_order),(pair_amount,base_amount) in execution__batch:
            result.append({'buy_order_id':buy_order.id,'sell_order_id':sell_order.id,'pair_amount':pair_amount,'base_amount':base_amount})
        return result

    @classmethod
    @log_variables_and_return
    def find_matched_orders_parallel(cls):
        cls.initialize()
        with ThreadPoolExecutor(max_workers=len(cls.token_pairs)) as executor:
            futures = []
            for token_pair in cls.token_pairs:
                futures.append(executor.submit(cls.find_matched_orders, token_pair))

    