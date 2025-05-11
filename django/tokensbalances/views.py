from django.shortcuts import render
from .serializers import GetTokenInformationSerializer
from .models import Token
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .services import *

@api_view(['GET'])
def get_all_tokens(request):
    tokens = get_tokens()
    serializer = GetTokenInformationSerializer(tokens, many=True)
    return Response(serializer.data)


