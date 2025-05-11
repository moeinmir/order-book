from rest_framework import serializers
from .models import CustomUser

class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)
    eth_address = serializers.CharField(read_only=True)
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number', 'first_name','last_name','password','eth_address']
  