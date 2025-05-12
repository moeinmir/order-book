from django.shortcuts import render
from .serializers import GetTokenInformationSerializer
from .models import Token
from utils.contracthelper import get_token_contract, transfer_token;
from accounts.services import UserService
from .models import AccountBalance
from django.db import transaction
import logging

logger = logging.getLogger(__name__)



class TokenBalanceService:

    @staticmethod
    def get_tokens():
        return Token.objects.all()

    @staticmethod
    def get_token_by_id(token_id):
        return Token.objects.get(id=token_id)
    
    @staticmethod
    def fetch_update_get_user_token_balance(token_id, user_id):
        token = TokenBalanceService.get_token_by_id(token_id)
        user = UserService.get_user_by_id(user_id)
        contract = get_token_contract(token.address, token.type)
        user_address = user.eth_address
        account_balance, created = AccountBalance.objects.get_or_create(
            user_id=user_id, 
            token_id=token_id, 
            defaults={"total_balance": 0, "locked_amount": 0, "free_amount": 0, "is_locked": False}
        )
        if account_balance.is_locked:
            return (False, account_balance)            
        with transaction.atomic():
            if not account_balance.is_locked:
                account_balance.is_locked = True
                account_balance.save()
            try:
                balance= contract.functions.balanceOf(user_address).call()
            except Exception as e:
                transaction.set_rollback(True)
                return (False, account_balance)
            account_balance.total_balance = balance
            account_balance.free_amount = balance - account_balance.locked_amount
            account_balance.is_locked = False 
            account_balance.save()
            return (True, account_balance)


    @staticmethod
    def fetch_withdraw_update_user_token_balance(token_id, user_id, withdraw_amount,to_address):
        logger.info(f'token_id:{token_id},user_id:{user_id},withdraw_amount:{withdraw_amount},to_address:{to_address}')
        token = TokenBalanceService.get_token_by_id(token_id)
        logger.info(f'token:{token}')
        user = UserService.get_user_by_id(user_id)
        logger.info(f'user:{user}')
        contract = get_token_contract(token.address, token.type)
        logger.info(f'contract:{contract}')
        user_address = user.eth_address
        logger.info(f'user_address:{user_address}')
        account_balance = AccountBalance.objects.get(
            user_id=user_id, 
            token_id=token_id, 
        )
        logger.info(f'account_balance:{account_balance}')
        if account_balance.is_locked:
            return (False, account_balance,"")            
        with transaction.atomic():
            if not account_balance.is_locked:
                logger.info('it is not locked')
                account_balance.is_locked = True
                account_balance.save()
            try:
                balance= contract.functions.balanceOf(user_address).call()
                logger.info(f'the balance:{balance}')
            except Exception as e:
                transaction.set_rollback(True)
                return (False, account_balance,"")
            account_balance.total_balance = balance
            logger.info('balance is updated')
            account_balance.free_amount = balance - account_balance.locked_amount
            logger.info('the locked amount considered')
            if(account_balance.free_amount>withdraw_amount):
                logger.info('have enough balance')
                tx = transfer_token(user_address,to_address,withdraw_amount,token.address,token.type,user.eth_index)       
                account_balance.free_amount = account_balance.free_amount - withdraw_amount    
            account_balance.is_locked = False 
            account_balance.save()
            return (True, account_balance,tx)
