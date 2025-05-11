from rest_framework import serializers
from .models import CustomUser

class RegisterRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number', 'first_name','last_name','password']


class RegisterResponseSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number', 'first_name','last_name','eth_address']
    

class GetUserAccountInformationSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number', 'first_name','last_name','eth_address']
    

