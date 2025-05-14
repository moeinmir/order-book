from rest_framework import serializers
from .models import *

class GetTokenInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = '__all__'

class GetAccountTokenBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountBalance
        fields = '__all__'

class WithdrawTokenRequestSerializer(serializers.Serializer):
    to_address = serializers.CharField(max_length=100)
    withdraw_amount = serializers.CharField(max_length=50)    
    
class WithdrawTokenResponseSerializer(serializers.Serializer):
    to_address = serializers.CharField(max_length=100)
    withdraw_amount = serializers.CharField(max_length=50)    
    token_id = serializers.CharField(max_length=100)
    free_amount = serializers.CharField(max_length=100)
    tx = serializers.CharField(max_length=100)
    


class ChargeTokenRequestSerializer(serializers.Serializer):
    charge_amount = serializers.CharField(max_length=50)    
    
class ChargeTokenResponseSerializer(serializers.Serializer):
    charged_amount = serializers.CharField(max_length=50)    
    token_id = serializers.CharField(max_length=100)
    free_amount = serializers.CharField(max_length=100)
    tx = serializers.CharField(max_length=100)

class MoveTokenToHdWalletRequestSerializer(serializers.Serializer):
    amount_to_be_moved = serializers.CharField(max_length=100)
    
class MoveTokenToHdWalletResponseSerializer(serializers.Serializer):
    moved_amount = serializers.CharField(max_length=50)    
    token_id = serializers.CharField(max_length=100)
    remaining_amount = serializers.CharField(max_length=100)
    tx = serializers.CharField(max_length=100)
