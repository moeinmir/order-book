from django.test import TestCase


from django.test import TestCase
from .services.order_service import OrderService
from .services.match_orders_service import MatchOrdersService
from .services.schedule_execute_matched_orders import ScheduleExecuteMatchedOrders
from .services.schedule_finding_matched_orders import ScheduleFindingMatchedOrders
from utils.redisclient import RedisClient
#here we want to write a test that try to execute orders after sending fetching them from kafka but every time
#create a pair or orders that could match 
#make a batch and send it with logic you already have
#try to fetch it and consume it
from  confluent_kafka import Consumer
from django.conf import settings

faghani_user_id = 1
token_pair_id = 1

def test_pull_once(token_pair_id):
    topic = str(token_pair_id)
    consumer = Consumer(settings.KAFKA_CONFIG)
    consumer.subscribe(['1'])
    msg = consumer.poll(timeout=2.0)
    consumer.close()
    return msg

class ProductTestCase(TestCase):
    buy_limit = OrderService.add_order(faghani_user_id,token_pair_id,10,"LIMIT","BUY",1)    
    print(buy_limit)
    sell_market = OrderService.add_order(faghani_user_id,token_pair_id,10,"MARKET","SELL",1)
    print(sell_market)
    # match = MatchOrdersService.fill_sell_market_best_interest(token_pair_id)
    # print(match)
    # message_that_goes_to_kafka_and_we_expect_to_get_it_back_like_this = ScheduleFindingMatchedOrders.prepare_execution_batch_to_be_send_to_kafka(match)
    # print(message_that_goes_to_kafka_and_we_expect_to_get_it_back_like_this)
    
    # sell_order = OrderService.get_order_by_id(message_that_goes_to_kafka_and_we_expect_to_get_it_back_like_this[0]['sell_order_id'])
    # buy_order = OrderService.get_order_by_id(message_that_goes_to_kafka_and_we_expect_to_get_it_back_like_this[0]['buy_order_id'])
    # print(sell_order)
    # print(buy_order)

    # sell_required_account_balance = sell_order.required_token_account_balance
    # print(sell_required_account_balance)

    # sell_other_account_balance = sell_order.other_token_account_balance
    # print(sell_other_account_balance)

    # buy_required_account_balance = buy_order.required_token_account_balance
    # print(buy_required_account_balance)

    # buy_other_account_balance = buy_order.other_token_account_balance
    # print(buy_other_account_balance)

    # last_price = message_that_goes_to_kafka_and_we_expect_to_get_it_back_like_this[0]['base_amount']//message_that_goes_to_kafka_and_we_expect_to_get_it_back_like_this[0]['pair_amount']
    # RedisClient.set_item(sell_order.token_pair.id,last_price)
    # x = RedisClient.get_item(sell_order.token_pair.id)
    
    # RedisClient.set_item("x","y")
    # result = RedisClient.get_item("1")
    
    # ScheduleExecuteMatchedOrders.execute_batch(message_that_goes_to_kafka_and_we_expect_to_get_it_back_like_this)

    # response = ScheduleFindingMatchedOrders.send_execution_batch_to_kafka(match,token_pair_id)
    # print(response)

    # fetched_message_from_kafka = test_pull_once(token_pair_id)
    # print(fetched_message_from_kafka)

    # prepared_for_execution = ScheduleExecuteMatchedOrders.reverse_execution_batch_to_be_used_in_execution(fetched_message_from_kafka)
    # print(prepared_for_execution)    
    # ScheduleExecuteMatchedOrders.execute_batch(prepared_for_execution)

   
    pass    
    
