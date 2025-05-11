from django.shortcuts import render
from .serializers import GetTokenInformationSerializer
from .models import Token
from rest_framework.response import Response


def get_tokens():
    return Token.objects.all()
