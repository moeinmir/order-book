from rest_framework import serializers
from .models import *

class GetTokenInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = '__all__'


