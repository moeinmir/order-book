from django.shortcuts import render
from .serializers import *
from .services.order_service import OrderService
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated 
from drf_yasg.utils import swagger_auto_schema
import logging
logger = logging.getLogger(__file__)

@api_view(['GET'])
def get_all_token_pairs(request):
    token_pairs = OrderService.get_token_pairs()
    serializer = GetTokenPairsResponseSerializer(token_pairs,many=True)
    return Response(serializer.data,status = 200)    

@swagger_auto_schema(
    method='post',
    request_body = AddOrderRequestSerializer,
    responses={200: AddOrderResponseSerializer}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_order_for_me(request):
    logger.info(f'request:{request}')
    user = request.user
    logger.info(f'user: {user.id}')
    add_order_request_serializer = AddOrderRequestSerializer(data = request.data)  
    logger.info(f'add_order_request_serializer: {add_order_request_serializer}')  
    if not add_order_request_serializer.is_valid():
        logger.error(f'invalid data:{add_order_request_serializer}')
        return Response(add_order_request_serializer.errors,status=400)
    
    amount = add_order_request_serializer.data['amount']
    logger.info(f'amount:{amount}')
    type = add_order_request_serializer.data['type']
    logger.info(f'type:{type}')
    direction = add_order_request_serializer.data['direction']
    logger.info(f'direction:{direction}')
    limit_price = add_order_request_serializer.validated_data.get('limit_price')
    logger.info(f'limit_price:{limit_price}')
    token_pair_id = add_order_request_serializer.data['token_pair_id']
    logger.info(f'token_pair_id:{token_pair_id}')
    success ,result = OrderService.add_order(user.id,token_pair_id,int(amount),type,direction,int(limit_price))
    if(success):
        add_order_response_serializer = AddOrderResponseSerializer(result)
        return Response(add_order_response_serializer.data,status=200)
    else:
        return Response(None,status=400)


@api_view(['GET'])
def get_all_orders(request):
    orders = OrderService.get_orders()
    serializer = GetOrderResponseSerializer(orders,many=True)
    return Response(serializer.data,status=200)
