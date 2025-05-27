from ..models import TokenPair
from ..models import Order
from tokensbalances.models import AccountBalance
from django.db import transaction
from accounts.services import UserService
import logging
import time
from threading import Lock
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, wait
logger = logging.getLogger(__name__)
import queue
from functools import wraps
from utils.logwrraper import log_variables_and_return
from utils.kafkaproducer import *
from .order_service import OrderService
from utils.redisclient import RedisClient

@staticmethod
def atomic_change_status_active_to_waiting_for_execution_wrapper(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        batch = func(*args, **kwargs)
        if not batch:
            return batch

        unique_orders = set()
        for (buy_order, sell_order), _ in batch:
            unique_orders.add(buy_order)
            unique_orders.add(sell_order)

        for order in unique_orders:
            order.atomic_change_status_active_to_waiting_for_execution()

        return batch
    return wrapper 
   
class MatchOrdersService():     
    @atomic_change_status_active_to_waiting_for_execution_wrapper
    @log_variables_and_return
    def fill_sell_market_best_interest(token_pair_id):
        with transaction.atomic():
            source_sell_market = Order.objects.get_active_unlocked(token_pair_id).filter(direction='SELL', type='MARKET').order_by('created_at').first()
            if not source_sell_market:return []
            target_buy_limit = Order.objects.get_active_unlocked(token_pair_id).filter(direction='BUY', type='LIMIT').order_by('-limit_price').first()
            target_buy_market = Order.objects.get_active_unlocked(token_pair_id).filter(direction='BUY', type='MARKET').order_by('created_at').first()
            if not target_buy_limit and not target_buy_market:return []
            source_amount = source_sell_market.remaining_amount
            batch = []
            if target_buy_limit and not target_buy_market:
                price = target_buy_limit.limit_price
                amount = min(source_amount, target_buy_limit.remaining_amount)
                fund = amount * price
                batch.append(((target_buy_limit, source_sell_market), (amount, fund)))
                return batch
            if target_buy_market:
                last_price = RedisClient.get_item(token_pair_id)
                if not last_price or last_price <= 0:return []
                limit_price = target_buy_limit.limit_price if target_buy_limit else 0
                limit_amount = target_buy_limit.remaining_amount if target_buy_limit else 0
                market_fund = target_buy_market.remaining_amount 
                market_amount = market_fund // last_price
                if target_buy_limit and limit_price > last_price:
                    fillable_limit_amount = min(limit_amount, source_amount)
                    fillable_limit_fund = fillable_limit_amount * limit_price
                    batch.append(((target_buy_limit, source_sell_market), (fillable_limit_amount, fillable_limit_fund)))
                    source_amount -= fillable_limit_amount
                    if source_amount > 0:
                        fillable_market_amount = min(market_amount, source_amount)
                        fillable_market_fund = fillable_market_amount * last_price
                        batch.append(((target_buy_market, source_sell_market), (fillable_market_amount, fillable_market_fund)))
                else:
                    fillable_market_amount = min(market_amount, source_amount)
                    fillable_market_fund = fillable_market_amount * last_price
                    batch.append(((target_buy_market, source_sell_market), (fillable_market_amount, fillable_market_fund)))
                    source_amount -= fillable_market_amount
                    if target_buy_limit and source_amount > 0:
                        fillable_limit_amount = min(limit_amount, source_amount)
                        fillable_limit_fund = fillable_limit_amount * limit_price
                        batch.append(((target_buy_limit, source_sell_market), (fillable_limit_amount, fillable_limit_fund)))
            return batch
    
    @atomic_change_status_active_to_waiting_for_execution_wrapper
    @log_variables_and_return
    def fill_buy_market_best_interest(token_pair_id):
        with transaction.atomic():
            source_buy_market = Order.objects.get_active_unlocked(token_pair_id).filter(direction='BUY', type='MARKET').order_by('created_at').first()
            if not source_buy_market:return []
            target_sell_limit = Order.objects.get_active_unlocked(token_pair_id).filter(direction='SELL', type='LIMIT').order_by('limit_price').first()
            target_sell_market = Order.objects.get_active_unlocked(token_pair_id).filter(direction='SELL', type='MARKET').order_by('created_at').first()
            if not target_sell_limit and not target_sell_market:return []
            source_fund = source_buy_market.remaining_amount
            batch = []
            if target_sell_limit and not target_sell_market:
                price = target_sell_limit.limit_price
                max_amount = source_fund / price
                amount = min(target_sell_limit.remaining_amount, max_amount)
                fund = amount * price
                batch.append(((target_sell_limit, source_buy_market), (amount, fund)))
                return batch
            if target_sell_market:
                last_price = RedisClient.get_item(token_pair_id)
                if not last_price or last_price <= 0: return []
                limit_price = target_sell_limit.limit_price if target_sell_limit else float('inf')
                limit_amount = target_sell_limit.remaining_amount if target_sell_limit else 0
                market_amount = target_sell_market.remaining_amount
                if target_sell_limit and limit_price < last_price:
                    fillable_limit_amount = min(limit_amount, source_fund / limit_price)
                    fillable_limit_fund = fillable_limit_amount * limit_price
                    batch.append(((target_sell_limit, source_buy_market), (fillable_limit_amount, fillable_limit_fund)))
                    source_fund -= fillable_limit_fund
                    if source_fund > 0:
                        fillable_market_amount = min(market_amount, source_fund / last_price)
                        fillable_market_fund = fillable_market_amount * last_price
                        batch.append(((target_sell_market, source_buy_market), (fillable_market_amount, fillable_market_fund)))
                else:
                    fillable_market_amount = min(market_amount, source_fund / last_price)
                    fillable_market_fund = fillable_market_amount * last_price
                    batch.append(((target_sell_market, source_buy_market), (fillable_market_amount, fillable_market_fund)))
                    source_fund -= fillable_market_fund
                    if target_sell_limit and source_fund > 0:
                        fillable_limit_amount = min(limit_amount, source_fund / limit_price)
                        fillable_limit_fund = fillable_limit_amount * limit_price
                        batch.append(((target_sell_limit, source_buy_market), (fillable_limit_amount, fillable_limit_fund)))
            return batch
    
    @atomic_change_status_active_to_waiting_for_execution_wrapper
    @log_variables_and_return
    def fill_sell_limit_best_interest( token_pair_id):
        with transaction.atomic():    
            source_sell_limit = Order.objects.get_active_unlocked(token_pair_id).filter(direction='SELL', type='LIMIT').order_by('limit_price').first()
            if not source_sell_limit: return[]
            target_buy_limit = Order.objects.get_active_unlocked(token_pair_id).filter(direction='BUY', type='LIMIT').order_by('-limit_price').first()
            target_buy_market = Order.objects.get_active_unlocked(token_pair_id).filter(direction='BUY', type='MARKET').order_by('created_at').first()
            if not target_buy_limit and not target_buy_market: return[]

            if not target_buy_limit or (target_buy_market.remaining_amount / source_sell_limit.limit_price) >= source_sell_limit.remaining_amount:
                amount = source_sell_limit.remaining_amount
                price = source_sell_limit.limit_price
                fund = price * amount
                return [((target_buy_market, source_sell_limit), (amount, fund))]

            source_sell_limit_price = source_sell_limit.limit_price
            target_buy_limit_price = target_buy_limit.limit_price
            is_target_limit_good_for_source_limit = True if source_sell_limit_price <= target_buy_limit_price else False
            if not target_buy_market:
                if not is_target_limit_good_for_source_limit: return []
                price = target_buy_limit_price
                amount = min(target_buy_limit.remaining_amount, source_sell_limit.remaining_amount)
                fund = price * amount
                return [((target_buy_limit, source_sell_limit), (amount, fund))]
            source_sell_limit_amount = source_sell_limit.remaining_amount
            target_buy_market_fund = target_buy_market.remaining_amount
            source_vs_market_amount = min(source_sell_limit_amount, target_buy_market_fund / source_sell_limit.limit_price)
            source_vs_market_price = source_sell_limit.limit_price
            source_vs_market_fund = source_vs_market_amount * source_vs_market_price
            batch = [((target_buy_market, source_sell_limit), (source_vs_market_amount, source_vs_market_fund))]
            source_remaining_amount = source_sell_limit_amount - source_vs_market_amount
            if is_target_limit_good_for_source_limit and source_remaining_amount > 0:
                amount = min(target_buy_limit.remaining_amount, source_remaining_amount)
                price = target_buy_limit.limit_price
                fund = amount * price
                batch.append(((target_buy_limit, source_sell_limit), (amount, fund)))
            return batch
    
    @atomic_change_status_active_to_waiting_for_execution_wrapper
    @log_variables_and_return        
    def fill_buy_limit_best_interest(token_pair_id):
        with transaction.atomic():    
            source_buy_limit = Order.objects.get_active_unlocked(token_pair_id).filter(direction='BUY',type='LIMIT').order_by('-limit_price').first()
            if not source_buy_limit: return[]
            target_sell_limit = Order.objects.get_active_unlocked(token_pair_id).filter(direction='SELL',type='LIMIT').order_by('limit_price').first()
            target_sell_market = Order.objects.get_active_unlocked(token_pair_id).filter(direction='SELL',type='MARKET').order_by('created_at').first()
            if not target_sell_limit and not target_sell_market: return[]            
            if not target_sell_limit or source_buy_limit.remaining_amount <= target_sell_market.remaining_amount:
                amount = min(target_sell_market.remaining_amount,  source_buy_limit.remaining_amount)   
                price = source_buy_limit.limit_price
                fund = price*amount
                return [((target_sell_market,source_buy_limit),(amount,fund))]   
            source_buy_limit_price = source_buy_limit.limit_price
            target_sell_limit_price = source_buy_limit.limit_price
            is_target_limit_good_for_source_limit = False if source_buy_limit_price<target_sell_limit_price else True
            if not target_sell_market:
                if not is_target_limit_good_for_source_limit: return[]
                price = target_sell_limit_price
                amount = min(target_sell_limit.remaining_amount , source_buy_limit.remaining_amount)
                fund = price*amount
                return[((target_sell_limit,source_buy_limit),(amount,fund))]
            source_buy_limit_amount = source_buy_limit.remaining_amount
            target_buy_market_amount = target_sell_market.remaining_amount
            source_vs_market_amount = target_buy_market_amount
            source_remaining_amount = source_buy_limit_amount - source_vs_market_amount
            source_vs_limit_amount = source_remaining_amount - source_vs_market_amount
            source_vs_market_price = source_buy_limit.limit_price 
            source_vs_limit_price = target_sell_limit.limit_price
            source_vs_market_fund = source_vs_market_amount*source_vs_market_price
            source_vs_limit_fund = source_vs_limit_amount*source_vs_limit_price         
            batch = [(target_sell_market,source_buy_limit),(source_vs_market_amount,source_vs_market_fund)]
            if is_target_limit_good_for_source_limit and source_vs_limit_fund>0 and source_vs_limit_amount>0:
                batch.append(((target_sell_limit,source_buy_limit),(source_vs_limit_amount,source_vs_limit_fund)))
            return batch





