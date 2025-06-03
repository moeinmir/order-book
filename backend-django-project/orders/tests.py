from django.test import TestCase

from django.test import TestCase, TransactionTestCase
from .services.order_service import OrderService
from .services.match_orders_service import MatchOrdersService
from .services.schedule_execute_matched_orders import ScheduleExecuteMatchedOrders
from .services.schedule_finding_matched_orders import ScheduleFindingMatchedOrders
from utils.redisclient import RedisClient
from  confluent_kafka import Consumer
from django.conf import settings
from dataclasses import dataclass
from tokensbalances.models import AccountBalance
from .models import Order
from accounts.models import CustomUser
import time
from accounts.services import UserService
from accounts.serializers import RegisterRequestSerializer
from django.conf import settings
from tokensbalances.services import TokenBalanceService
from .services.order_service import OrderService
from tokensbalances.models import AccountBalance
import random
from django.test import override_settings
import pytest

@dataclass
class AddOrderData:
    user_id: int
    token_pair_id: int
    amount: int
    type: str
    direction: str
    price: str

test_buyers = [
    {
        'username':"b1",
        'email':'b1@gmail.com' ,
        'phone_number':'phonenumber', 
        'first_name':'fistname',
        'last_name':'lastname',
        'password':'123'},
        {
        'username':"b2",
        'email':'b2@gmail.com' ,
        'phone_number':'phonenumber', 
        'first_name':'fistname',
        'last_name':'lastname',
        'password':'123'},
        {
        'username':"b3",
        'email':'b3@gmail.com' ,
        'phone_number':'phonenumber', 
        'first_name':'fistname',
        'last_name':'lastname',
        'password':'123'},
        {
        'username':"b4",
        'email':'b4@gmail.com' ,
        'phone_number':'phonenumber', 
        'first_name':'fistname',
        'last_name':'lastname',
        'password':'123'}
]

test_sellers = [
    {
        'username':"s1",
        'email':'s1@gmail.com' ,
        'phone_number':'phonenumber', 
        'first_name':'fistname',
        'last_name':'lastname',
        'password':'123'},
        {
        'username':"s2",
        'email':'s2@gmail.com' ,
        'phone_number':'phonenumber', 
        'first_name':'fistname',
        'last_name':'lastname',
        'password':'123'},
        {
        'username':"s3",
        'email':'s3@gmail.com' ,
        'phone_number':'phonenumber', 
        'first_name':'fistname',
        'last_name':'lastname',
        'password':'123'},
        {
        'username':"s4",
        'email':'s4@gmail.com' ,
        'phone_number':'phonenumber', 
        'first_name':'fistname',
        'last_name':'lastname',
        'password':'123'}
]

test_token_pair_id = 1
master_eth_index = settings.CENTRAL_HD_WALLET_INDEX

def reverse_orders_and_balances(buyers,sellers,token_pair):
    for user in test_buyers + test_sellers:
        user = UserService.get_user_by_username(user['username'])
        print(user)
        base_balance = AccountBalance.objects.filter(user = user, token = token_pair.base_token).first()
        print(base_balance.free_amount)
        pair_balance = AccountBalance.objects.filter(user = user, token = token_pair.pair_token).first()
        base_balance.free_amount = 4000
        pair_balance.free_amount = 4000
        base_balance.locked_amount = 0
        pair_balance.locked_amount = 0
        orders = Order.objects.filter(user= user)
        base_balance.save()
        pair_balance.save()
        for order in orders:
            order.delete()   
     
class CreateUsersAndChargeTheyAccountsOnceSoWeWillBeReadyForTest(TransactionTestCase):
    test_token_pair = OrderService.get_token_pair_by_id(test_token_pair_id)   
    reverse_orders_and_balances(test_buyers,test_sellers,test_token_pair)
    master_user = UserService.get_user_by_eth_index(master_eth_index)  
    master_base_balance = AccountBalance.objects.filter(user=master_user,token = test_token_pair.base_token).first()
    if not master_base_balance: success, master_base_balance = TokenBalanceService.fetch_update_get_user_hd_wallet_balance(test_token_pair.base_token.id,master_user.id)
    master_pair_balance = AccountBalance.objects.filter(user=master_user,token = test_token_pair.pair_token).first()
    if not master_pair_balance: success, master_pair_balance = TokenBalanceService.fetch_update_get_user_hd_wallet_balance(test_token_pair.pair_token.id,master_user.id)
    for user in test_buyers + test_sellers: 
        user = CustomUser.objects.filter(username=user['username'])
        if not user.first():
            register_user_serializer = RegisterRequestSerializer(data = {
                    'username':user['username'],
                    'email':user['email'] ,
                    'phone_number':user['phone_number'], 
                    'first_name':user['first_name'],
                    'last_name': user['last_name'],
                    'password':user['password']}
            )
            if register_user_serializer.is_valid():
                user = UserService.create_user(register_user_serializer.data)    
                success, base_balance = TokenBalanceService.fetch_update_get_user_hd_wallet_balance(test_token_pair.base_token.id,user.id)        
                time.sleep(3)
                success, pair_balance = TokenBalanceService.fetch_update_get_user_hd_wallet_balance(test_token_pair.pair_token.id,user.id)
                time.sleep(3)
                master_base_balance.free_amount = master_base_balance.free_amount - 1000
                master_pair_balance.free_amount = master_pair_balance.free_amount - 1000
                base_balance.free_amount = base_balance.free_amount + 1000
                pair_balance.free_amount = pair_balance.free_amount + 1000
                master_base_balance.save()
                master_pair_balance.save()
                base_balance.save()
                pair_balance.save()
        
    pair_provided_remaining_amount = 400
    pair_requested_remaining_amount_by_limit = 400
    number_of_sell_orders = random.randint(5,10)
    number_of_buy_limit_orders = random.randint(5,10)
    orders = []
    for i in range(number_of_sell_orders):
        random_seller_index = random.randint(0,len(test_sellers)-1)
        username = test_sellers[random_seller_index]['username']
        random_seller = UserService.get_user_by_username(username)
        random_amount = pair_provided_remaining_amount if i == (number_of_sell_orders -1) else random.randint(1,40)
        random_type_int = random.randint(0,1)
        random_type = 'LIMIT' if random_type_int == 0 else 'MARKET'
        random_price = random.randint(1,4)
        orders.append(AddOrderData(random_seller.id,test_token_pair_id,random_amount, random_type,'SELL',random_price))
        pair_provided_remaining_amount = pair_provided_remaining_amount - random_amount
    
    for i in range(number_of_buy_limit_orders):
        random_buyer = random.randint(0,len(test_buyers)-1)
        username = test_buyers[random_buyer]['username']
        random_buyer = UserService.get_user_by_username(username)    
        random_amount = random.randint(1,40)
        if i == (number_of_buy_limit_orders -1):
            random_amount = pair_requested_remaining_amount_by_limit
        random_price = random.randint(1,4)
        orders.append(AddOrderData(random_buyer.id,test_token_pair_id,random_amount,'LIMIT','BUY',random_price))
        pair_requested_remaining_amount_by_limit = pair_requested_remaining_amount_by_limit - random_amount
    print(orders)
    for order in orders:
        OrderService.add_order(order.user_id,order.token_pair_id,order.amount,order.type,order.direction,order.price)
    