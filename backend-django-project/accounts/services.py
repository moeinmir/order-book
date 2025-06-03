
from .models import CustomUser
from utils.hdwallethelper import derive_eth_address
from django.db import models

class UserService:
    @staticmethod
    def create_user(validated_data):
        next_index = (CustomUser.objects.aggregate(models.Max('eth_index'))['eth_index__max'] or 0) + 1
        keys = derive_eth_address(next_index)
        validated_data['eth_address'] = keys['address']
        validated_data['eth_index'] = next_index
        user = CustomUser.objects.create_user(**validated_data)
        return user
    
    @staticmethod
    def get_user_by_id(user_id):
        return CustomUser.objects.get(id=user_id)

    def get_user_by_username(username):
        user = CustomUser.objects.get(username = username)
        return user
    
    def get_user_by_eth_index(eth_index):
        return CustomUser.objects.get(eth_index=eth_index)