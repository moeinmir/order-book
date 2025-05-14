from .models import TokenPair
from .models import Order
from tokensbalances.models import AccountBalance
from django.db import transaction
from accounts.services import UserService

import logging
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
            logger.info(f'required_token__id: {required_token_id}')
            user_token_balance = AccountBalance.objects.filter(user=user_id,token = required_token_id).first()
            logger.info(f'user_token-balance:{user_token_balance}')
            locked = user_token_balance.lock_if_not()
            if not locked:
                logger.error(f'token balance record is locked')
                return(False, user_token_balance)
            if (direction == Order.OrderDirection.SELL ):
                required_token_amount = amount
            elif(type==Order.OrderType.LIMIT):
                required_token_amount = amount*limit_price
            else:    
                #here it means i will to pay amount to get what ever if can
                required_token_amount = amount
            
            if (user_token_balance.free_amount < required_token_amount):
                logger.error(f'insufficient balance')
                transaction.set_rollback(True)
                return (False,user_token_balance)
            else:
                user = UserService.get_user_by_id(user_id)
                user_token_balance.free_amount = user_token_balance.free_amount - required_token_amount
                user_token_balance.locked_amount = user_token_balance.locked_amount + required_token_amount
                user_token_balance.is_locked = False
                user_token_balance.save()
                order = Order()    
                order.user = user
                order.amount = amount
                order.type = type
                order.direction = direction
                order.token_pair = token_pair
                order.limit_price = limit_price    
                order.save()
            return (True,order)  
        

    def get_orders():
        return Order.objects.all()

class MatchOrdersService():    
    token_pairs = OrderService.get_token_pairs()
    best_sell_price = {}
    best_buy_price = {}
    last_sell_price = {}
    last_buy_price = {}
    execution_batches = {}
    
    @classmethod
    def initialize_price_tracking(cls):
        token_pairs = OrderService.get_token_pairs()
        for token_pair in token_pairs:
            id = token_pair.id
            cls.best_sell_price[id] = 0
            cls.best_buy_price[id] = 0
            cls.last_sell_price[id] = 0
            cls.last_buy_price[id] = 0
            cls.execution_batches[id] = []
    
    #we suppose these processes wont be executed together and we will find a way to do that
    def fill_sell_market_best_interest(self,token_pair_id):
        sell_side = Order.objects.active_unlocked_sell_market(token_pair_id).order_by('created_at').first()
        buy_side_limit = Order.objects.active_unlocked_buy_limit(token_pair_id).order_by('-limit_price').first()
        buy_side_market = Order.objects.active_unlocked_buy_market(token_pair_id).order_by('created_at').first()
        limit_price = buy_side_limit.limit_price
        current_price = self.best_sell_price[token_pair_id]
        current_price = limit_price if current_price < limit_price else current_price
        amount_to_be_filled = sell_side.remaining_amount
        limit_amount = buy_side_limit.amount
        market_amount = buy_side_market.amount
        total_provided_amount = limit_amount + market_amount
        if(amount_to_be_filled > total_provided_amount):
            return []
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
        return
    
    def fill_sell_limit_best_interest(self,token_pair_id):
        return
    
    def fill_buy_limit_best_interest(self,token_pair_id):
        return


    def find_matched_orders(cls):
        for token_pair in cls.token_pairs():
            execution_batch = cls.fill_sell_market_best_interest(token_pair.id)
            cls.execution_batches[token_pair.id].append(execution_batch) 
            execution_batch = cls.fill_sell_limit_best_interest(token_pair.id)
            cls.execution_batches[token_pair.id].append(execution_batch) 
            execution_batch = cls.fill_buy_market_best_interest(token_pair.id)
            cls.execution_batches[token_pair.id].append(execution_batch) 
            execution_batch = cls.fill_buy_limit_best_interest(token_pair.id)
            cls.execution_batches[token_pair.id].append(execution_batch) 
        

    def execute_batch(cls):
        return

    def execute_batches(cls):
        for token_pair in cls.token_pairs():
            current_batch = cls.execution_batches[token_pair.id].pop()
            cls.execute_batch(current_batch)
        return
       
