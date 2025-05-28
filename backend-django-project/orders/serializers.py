from rest_framework import serializers
from .models import *

class GetTokenPairsResponseSerializer(serializers.ModelSerializer):

    class Meta:
        model = TokenPair
        fields = '__all__'


class AddOrderRequestSerializer(serializers.Serializer):
    amount = serializers.CharField(max_length=100)
    type = serializers.CharField(max_length=100)
    direction = serializers.CharField(max_length=100)
    limit_price = serializers.CharField(max_length=100, default= 0)
    token_pair_id = serializers.IntegerField()

class AddOrderResponseSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Order 
        fields = '__all__'


class GetOrderResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"