from .models import TokenPair
from .models import Order
from tokensbalances.models import AccountBalance
from django.db import transaction
from accounts.services import UserService
import logging
import time
from threading import Lock
logger = logging.getLogger(__name__)

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

class MatchOrdersService():    
    token_pairs = []
    best_sell_price = {}
    best_buy_price = {}
    last_sell_price = {}
    last_buy_price = {}
    execution_batches = {}


    _lock = Lock()
    
    
    @classmethod
    def initialize(cls):
        token_pairs = OrderService.get_token_pairs()
        for token_pair in token_pairs:
            logger.info('initializing begin')
            id = token_pair.id
            cls.best_sell_price[id] = 0
            cls.best_buy_price[id] = 0
            cls.last_sell_price[id] = 0
            cls.last_buy_price[id] = 0
            cls.execution_batches[id] = []
            logger.info(f'token pairs:{token_pairs}')
            logger.info('initializing ended')
    
    #we suppose these processes wont be executed together and we will find a way to do that
    def fill_sell_market_best_interest(self,token_pair_id):
        with transaction.atomic():
            sell_side = Order.objects.get_active_unlocked(token_pair_id).filter(direction='sell',type='market').order_by('created_at').first()
            if not sell_side: return []
            buy_side_limit = Order.objects.get_active_unlocked(token_pair_id).filter(direction='buy',type='limit').order_by('-limit_price').first()
            buy_side_market = Order.objects.get_active_unlocked(token_pair_id).filter(direction='buy',type='market').order_by('created_at').first()
            if not buy_side_limit and not buy_side_market: return []
            current_price = self.best_sell_price[token_pair_id]
            limit_price = buy_side_limit.limit_price if buy_side_limit else current_price
            current_price = limit_price if current_price < limit_price else current_price
            amount_to_be_filled = sell_side.remaining_amount
            limit_amount = buy_side_limit.amount if buy_side_limit else 0
            market_amount = buy_side_market.amount if buy_side_market else 0
            total_provided_amount = limit_amount + market_amount
            if(market_amount==0):
                if not sell_side.lock_if_not(): raise Exception
                if not buy_side_limit.lock_if_not(): raise Exception  
                return [((sell_side,buy_side_limit),(limit_amount,limit_price*limit_amount))]   
            elif(limit_amount==0):
                if not sell_side.lock_if_not(): raise Exception
                if not buy_side_market.lock_if_not(): raise Exception  
                return [((sell_side,buy_side_market),(market_amount,current_price*limit_amount))]   
            elif(amount_to_be_filled == total_provided_amount):
                if not sell_side.lock_if_not(): raise Exception
                if not buy_side_limit.lock_if_not(): raise Exception  
                if not buy_side_market.lock_if_not(): raise Exception  
                return [((sell_side,buy_side_limit),(limit_amount,limit_price*limit_amount)),(sell_side,buy_side_market),(market_amount,current_price*market_amount)]
            elif(amount_to_be_filled<=market_amount):
                if not sell_side.lock_if_not(): raise Exception
                if not buy_side_limit.lock_if_not(): raise Exception  
                return [((sell_side,buy_side_market),(market_amount,current_price*amount_to_be_filled))]
            elif(amount_to_be_filled>market_amount):
                if not sell_side.lock_if_not(): raise Exception
                if not buy_side_limit.lock_if_not(): raise Exception  
                if not buy_side_market.lock_if_not(): raise Exception
                market_amount = amount_to_be_filled - limit_amount  
                return [((sell_side,buy_side_limit),(limit_amount,limit_price*limit_amount)),(sell_side,buy_side_market),(market_amount,current_price*market_amount)]
            else:
                if not sell_side.lock_if_not(): raise Exception
                if not buy_side_limit.lock_if_not(): raise Exception  
                return [((sell_side,buy_side_limit),(limit_amount,limit_price*limit_amount))]

    def fill_buy_market_best_interest(self,token_pair_id):
        with transaction.atomic():
            buy_side = Order.objects.get_active_unlocked(token_pair_id).filter(direction='buy',type='market').order_by('created_at').first()
            if not buy_side: return []
            sell_side_limit = Order.objects.get_active_unlocked(token_pair_id).filter(direction='sell',type='limit').order_by('limit_price').first()
            sell_side_market = Order.objects.get_active_unlocked(token_pair_id).filter(direction='sell',type='market').order_by('created_at').first()
            if not sell_side_limit and sell_side_market: return []
            current_price = self.best_buy_price[token_pair_id]
            limit_price = sell_side_limit.limit_price if sell_side_limit else current_price
            current_price = limit_price if current_price > limit_price else current_price        
            provide_fund = buy_side.remaining_amount
            limit_amount = sell_side_limit.amount if sell_side_limit else 0
            market_amount = sell_side_market.amount if sell_side_market else 0
            limit_required_fund = limit_amount*limit_price
            market_required_fund = market_amount*current_price    
            total_required_fund = limit_required_fund + market_required_fund
            if(market_amount==0):
                if not buy_side.lock_if_not(): raise Exception
                if not sell_side_limit.lock_if_not(): raise Exception  
                if(limit_price*limit_amount<provide_fund):            
                    return [((sell_side_limit,buy_side),(limit_amount,limit_price*limit_amount))]                       
                else:
                    return [((sell_side_limit,buy_side),(provide_fund//limit_price,provide_fund))]       
            elif(limit_amount==0):
                if not buy_side.lock_if_not(): raise Exception
                if not sell_side_market.lock_if_not(): raise Exception  
                if(current_price*market_amount<provide_fund):            
                    return [((sell_side_market,buy_side),(market_amount,current_price*market_amount))]                       
                else:
                    return [((sell_side_market,buy_side),(provide_fund//current_price,provide_fund))] 
            elif(total_required_fund<=provide_fund):
                if not buy_side.lock_if_not(): raise Exception
                if not sell_side_market(): raise Exception
                if not sell_side_limit(): raise Exception
                return [((sell_side_market,buy_side),(market_amount,current_price*market_amount)),((sell_side_limit,buy_side),(limit_amount,limit_price*limit_amount))]
            else:
                remaining_fund = provide_fund - current_price*market_amount
                return [((sell_side_market,buy_side),(market_amount,current_price*market_amount)),((sell_side_limit,buy_side),(remaining_fund//limit_price,remaining_fund))]


    def fill_sell_limit_best_interest(self,token_pair_id):
        with transaction.atomic():
            sell_side = Order.objects.get_active_unlocked(token_pair_id).filter(direction='sell',type='limit').order_by('limit_price').first()
            if not sell_side: return[]
            buy_side_market = Order.objects.get_active_unlocked(token_pair_id).filter(direction='buy',type='market').order_by('created_at').first()
            buy_side_limit = Order.objects.get_active_unlocked(token_pair_id).filter(direction='buy',type='limit').order_by('limit_price').first()
            if not buy_side_limit and buy_side_market: return[]

    def fill_buy_limit_best_interest(self,token_pair_id):
        return[]


    def find_matched_orders(cls):
        for token_pair in cls.token_pairs:
            execution_batch = cls.fill_sell_market_best_interest(token_pair.id)
            cls.execution_batches[token_pair.id].append(execution_batch) 
            execution_batch = cls.fill_sell_limit_best_interest(token_pair.id)
            cls.execution_batches[token_pair.id].append(execution_batch) 
            execution_batch = cls.fill_buy_market_best_interest(token_pair.id)
            cls.execution_batches[token_pair.id].append(execution_batch) 
            execution_batch = cls.fill_buy_limit_best_interest(token_pair.id)
            cls.execution_batches[token_pair.id].append(execution_batch) 
        

    def execute_batch(execution_batch):
        for (sell_order,buy_order),(pair_amount,base_amount) in execution_batch:
            MatchOrdersService.execute_order_pair(sell_order,buy_order,pair_amount,base_amount)

    def execute_order_pair(sell_order:Order,buy_order:Order,pairAmount,baseAmount):
        sell_required_account_balance = sell_order.required_token_account_balance
        sell_other_account_balance = sell_order.other_token_account_balance
        buy_required_account_balance = buy_order.required_token_account_balance
        buy_other_account_balance = buy_order.other_token_account_balance
        if not sell_required_account_balance.lock_if_not(): raise Exception
        if not sell_other_account_balance.lock_if_not(): raise Exception
        if not buy_required_account_balance.lock_if_not(): raise Exception
        if not sell_other_account_balance.lock_if_not(): raise Exception
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
        return

    def execute_batches(cls):
        logger.info("calling")
        while True:
            for token_pair in cls.token_pairs:
                current_batch = cls.execution_batches[token_pair.id].pop()
                cls.execute_batch(current_batch)
            
    @classmethod
    def find_and_execute_matches(cls):
        with cls._lock:
            cls.initialize()
            cls.find_matched_orders(cls)
            cls.execute_batches(cls)   