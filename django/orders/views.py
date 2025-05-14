from django.shortcuts import render
from .serializers import *
from .services import OrderService
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated 
from drf_yasg.utils import swagger_auto_schema

@api_view(['GET'])
def get_all_token_pairs():
    token_pairs = OrderService.get_token_pairs()
    serializer = GetTokenPairsResponse(token_pairs,many=True)
    return Response(serializer.data,status = 200)    

@swagger_auto_schema(
    method='post',
    request_body = AddOrderRequestSerializer,
    responses={200: AddOrderResponseSerializer}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_order_for_me(request):
    user = request.user
    add_order_request_serializer = AddOrderRequestSerializer(request)    
    if not add_order_request_serializer.is_valid():
        return Response(add_order_request_serializer.errors,status=400)
    
    amount = add_order_request_serializer.validate_data['amount']
    type = add_order_request_serializer.validate_data['amount']
    direction = add_order_request_serializer.validate_data['direction']
    limit_price = add_order_request_serializer.validate_data['limit_price']
    token_pair_id = add_order_request_serializer.validate_data['token_pair_id']
    success ,order = OrderService.add_order(user.id,token_pair_id,int(amount),type,direction,int(limit_price))
    add_order_response_serializer = AddOrderResponseSerializer(order)
    if(success):
        return Response(add_order_response_serializer.data,status=200)
    else:
        return Response(add_order_response_serializer.data,status=400)
