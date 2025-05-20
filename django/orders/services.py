from .models import TokenPair
from .models import Order
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
class OrderService():

    @staticmethod
    def get_token_pairs():
        logger.info('token_pairs')
        token_pairs = TokenPair.objects.all()
        logger.info(f'token pairs:{token_pairs}')
        return token_pairs

    @staticmethod
    def get_token_pair_by_id(token_id):
         return TokenPair.objects.get(id=token_id)

    @staticmethod
    def add_order(user_id, token_pair_id, amount,type,direction,limit_price):
        with transaction.atomic():
            logger.info(f'{user_id},{token_pair_id},{amount},{type},{direction},{limit_price}')
            token_pair = OrderService.get_token_pair_by_id(token_pair_id)
            logger.info(f'token_pair {token_pair}')
            required_token_id = token_pair.base_token.id if direction == Order.OrderDirection.BUY else token_pair.pair_token.id
            other_token_id = token_pair.base_token.id if direction == Order.OrderDirection.SELL else token_pair.pair_token.id
            logger.info(f'required_token__id: {required_token_id}')
            required_token_account_balance = AccountBalance.objects.filter(user=user_id,token = required_token_id).first()
            other_token_account_balance = AccountBalance.objects.filter(user=user_id,token = other_token_id).first()
            locked = required_token_account_balance.lock_if_not()
            if not locked:
                logger.error(f'token balance record is locked')
                return(False, required_token_account_balance)
            if (direction == Order.OrderDirection.SELL ):
                required_token_amount = amount
            elif(type==Order.OrderType.LIMIT):
                required_token_amount = amount*limit_price
            else:    
                #here it means i will to pay amount to get what ever if can
                required_token_amount = amount
            
            if (required_token_account_balance.free_amount < required_token_amount):
                logger.error(f'insufficient balance')
                transaction.set_rollback(True)
                return (False,required_token_account_balance)
            else:
                user = UserService.get_user_by_id(user_id)
                required_token_account_balance.free_amount = required_token_account_balance.free_amount - required_token_amount
                required_token_account_balance.locked_amount = required_token_account_balance.locked_amount + required_token_amount
                required_token_account_balance.is_locked = False
                required_token_account_balance.save()
                order = Order()    
                order.user = user
                order.amount = amount
                order.remaining_amount = amount
                order.type = type
                order.direction = direction
                order.token_pair = token_pair
                order.limit_price = limit_price  
                order.required_token_account_balance = required_token_account_balance 
                order.other_token_account_balance = other_token_account_balance 
                order.save()
            return (True,order)  
        
    def get_orders():
        return Order.objects.all()

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
    token_pairs = []
    best_sell_price = {}
    best_buy_price = {}
    last_sell_price = {}
    last_buy_price = {}
    last_price = {}
    execution_batches = {}
    _lock = Lock()

    @classmethod
    @log_variables_and_return
    def initialize(cls):
        cls.token_pairs = OrderService.get_token_pairs()
        for token_pair in cls.token_pairs:
            logger.info('initializing begin')
            id = token_pair.id
            cls.best_sell_price[id] = 1
            cls.best_buy_price[id] = 1
            cls.last_sell_price[id] = 1
            cls.last_buy_price[id] = 1
            cls.last_price[id] = 1
            cls.execution_batches[id] = Queue()
            logger.info(f'token pairs:{cls.token_pairs}')
            logger.info('initializing ended')
    
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
                last_price = MatchOrdersService.last_price[token_pair_id]
                if not last_price or last_price <= 0:return []
                limit_price = target_buy_limit.limit_price if target_buy_limit else 0
                limit_amount = target_buy_limit.remaining_amount if target_buy_limit else 0
                market_fund = target_buy_market.remaining_amount 
                market_amount = market_fund / last_price
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
                last_price = MatchOrdersService.last_price[token_pair_id]
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
            if is_target_limit_good_for_source_limit:
                batch.append(((target_sell_limit,source_buy_limit),(source_vs_limit_amount,source_vs_limit_fund)))
            return batch
    @classmethod
    @log_variables_and_return
    def find_matched_orders(cls,token_pair):
        logger.info("finding matches")
        logger.info(f"tokenpair,{token_pair}")
        while True:
            try:
                time.sleep(2)
                logger.info(f"token_pair:{token_pair}")
                execution_batch = cls.fill_sell_market_best_interest(token_pair.id)
                logger.info(f"execution bach:{execution_batch}")
                if len(execution_batch): cls.execution_batches[token_pair.id].put(execution_batch)  
                logger.info(f"execution bach:{execution_batch}")
            except:
                logger.error(f"Error matching orders {token_pair}: {e}")
            try:    
                execution_batch = cls.fill_sell_limit_best_interest(token_pair.id)
                logger.info(f"execution bach:{execution_batch}")
                if len(execution_batch): cls.execution_batches[token_pair.id].put(execution_batch)  
            except:
                logger.error(f"Error matching orders {token_pair}: {e}")
            try:   
                execution_batch = cls.fill_buy_market_best_interest(token_pair.id)
                logger.info(f"execution bach:{execution_batch}")
                if len(execution_batch): cls.execution_batches[token_pair.id].put(execution_batch)  
            except:
                logger.error(f"Error matching orders {token_pair}: {e}")
            try:    
                execution_batch = cls.fill_buy_limit_best_interest(token_pair.id)
                logger.info(f"execution bach:{execution_batch}")
                if len(execution_batch): cls.execution_batches[token_pair.id].put(execution_batch)   
            except Exception as e:
                logger.error(f"Error matching orders {token_pair}: {e}")
            logger.info("does execution batch getting filled")



    @classmethod
    @log_variables_and_return
    def find_matched_orders_parallel(cls):
        with ThreadPoolExecutor(max_workers=len(cls.token_pairs)) as executor:
            futures = []
            for token_pair in cls.token_pairs:
                futures.append(executor.submit(cls.find_matched_orders, token_pair))
    
    @classmethod
    @log_variables_and_return
    def execute_batch(cls,execution_batch):
        logger.info(f"executing batch:{execution_batch}")
        for (sell_order,buy_order),(pair_amount,base_amount) in execution_batch:
            
            logger.info(f"executing batch sell order:{sell_order}")
            logger.info(f"executing batch buy order:{buy_order}")
            logger.info(f"executing batch pair amount:{pair_amount}")
            logger.info(f"executing batch base amount:{base_amount}")
            last_price = pair_amount//base_amount
            
            cls.execute_order_pair(sell_order,buy_order,pair_amount,base_amount)
            cls.last_price[sell_order.token_pair.id] = last_price
    
    @log_variables_and_return
    def execute_order_pair(sell_order:Order,buy_order:Order,pairAmount,baseAmount):
        logger.info("executing order pair")
        
        logger.info(f"sell order: {sell_order}")
        logger.info(f"sell order: {buy_order}")
        logger.info(f"sell order: {pairAmount}")
        logger.info(f"sell order: {baseAmount}")

        sell_required_account_balance = sell_order.required_token_account_balance
        logger.info(f"sellorderrequiredaccountbalance:{sell_required_account_balance}")
        sell_other_account_balance = sell_order.other_token_account_balance
        buy_required_account_balance = buy_order.required_token_account_balance
        buy_other_account_balance = buy_order.other_token_account_balance
        if not sell_required_account_balance.lock_if_not(): raise Exception
        # if not sell_other_account_balance.lock_if_not(): raise Exception
        if not buy_required_account_balance.lock_if_not(): raise Exception
        # if not sell_other_account_balance.lock_if_not(): raise Exception
        sell_required_account_balance.locked_amount = sell_required_account_balance.locked_amount - pairAmount
        sell_other_account_balance.free_amount = sell_other_account_balance.free_amount + baseAmount
        buy_required_account_balance.locked_amount = buy_other_account_balance.locked_amount - baseAmount
        buy_other_account_balance.free_amount = buy_other_account_balance.free_amount + pairAmount
        sell_order.remaining_amount = sell_order.remaining_amount - pairAmount
        if (buy_order.OrderType == Order.OrderType.LIMIT):
            buy_order.remaining_amount = buy_order.remaining_amount - pairAmount
        else:
            buy_order.remaining_amount = buy_order.remaining_amount - baseAmount   
        sell_order.see_if_it_is_complete_and_save()
        buy_order.see_if_it_is_complete_and_save()    
        sell_required_account_balance.unlock_and_save()
        sell_other_account_balance.unlock_and_save()
        buy_required_account_balance.unlock_and_save()
        buy_other_account_balance.unlock_and_save()
        

    @classmethod
    @log_variables_and_return
    def execute_batch_worker(cls, token_pair):
        logger.info("execution batch worker")
        while True:
            logger.info("execution batch info")
            time.sleep(2)
            try:
                
                current_batch = cls.execution_batches[token_pair.id].get(timeout=2)
                logger.info(f"current batch in execution:{current_batch}")
                if current_batch:
                    logger.info(f"current batch to be executed: {current_batch}")
                    cls.execute_batch(current_batch)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing batch for {token_pair}: {e}")

    @classmethod
    @log_variables_and_return
    def execute_batches_parallel(cls):
        with ThreadPoolExecutor(max_workers=len(cls.token_pairs)) as executor:
            futures = []
            for token_pair in cls.token_pairs:
                futures.append(executor.submit(cls.execute_batch_worker, token_pair))
                
    @classmethod
    def find_and_execute_matches(cls):
        with cls._lock:
            cls.initialize()
            with ThreadPoolExecutor(max_workers=2) as executor:
                executor.submit(cls.find_matched_orders_parallel)
                executor.submit(cls.execute_batches_parallel)
                