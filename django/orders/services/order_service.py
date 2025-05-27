from ..models import TokenPair
from ..models import Order
from tokensbalances.models import AccountBalance
from django.db import transaction
from accounts.services import UserService
import logging
logger = logging.getLogger(__name__)
from functools import wraps
from utils.kafkaproducer import *
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
    
    def get_order_by_id(order_id):
        return Order.objects.get(id=order_id)
