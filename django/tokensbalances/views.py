from django.shortcuts import render
from .serializers import GetTokenInformationSerializer
from .models import Token
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .services import TokenBalanceService
from .serializers import *
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
def get_all_tokens(request):
    tokens = TokenBalanceService.get_tokens()
    serializer = GetTokenInformationSerializer(tokens, many=True)
    return Response(serializer.data,status=200)

token_id_param = openapi.Parameter(
    name='token_id',
    in_=openapi.IN_QUERY,
    description="ID of the token",
    type=openapi.TYPE_INTEGER,
    required=True
)

@swagger_auto_schema(
    method='get',
    manual_parameters=[token_id_param],
    responses={200: GetAccountTokenBalanceSerializer}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_token_balance(request):
    logger.info(f'request:{request}')
    user = request.user
    logger.info(f'user:{user}')
    token_id = request.query_params.get("token_id")
    logger.info(f'token_id:{token_id}')
    success, account_balance = TokenBalanceService.fetch_update_get_user_hd_wallet_balance(token_id,user.id)
    logger.info(f'account_balance:{account_balance}')
    logger.info(f'success:{success}')
    get_account_token_balance_serializer = GetAccountTokenBalanceSerializer(account_balance)
    logger.info(f'get_account_token_balance_serializer:{get_account_token_balance_serializer.data}')
    if(success):
        return Response(get_account_token_balance_serializer.data,status=200)
    else:    
        return Response(get_account_token_balance_serializer.data,status=400)

@swagger_auto_schema(
    method='post',
    manual_parameters=[token_id_param],
    request_body = WithdrawTokenRequestSerializer,
    responses={200: WithdrawTokenResponseSerializer}
)
@api_view(['post'])
@permission_classes([IsAuthenticated])
def withdraw_token(request):
    logger.info(f'request:{request}')
    user = request.user
    logger.info(f'user:{user}')
    token_id = request.query_params.get("token_id")
    logger.info(f'token_id:{token_id}')
    withdraw_token_request_serializer = WithdrawTokenRequestSerializer(data=request.data)

    if not withdraw_token_request_serializer.is_valid():
        logger.error("invalid body")
        return Response(withdraw_token_request_serializer.errors, status=400)

    logger.info(f'withdraw_token_request_serializer: {withdraw_token_request_serializer}')
    to_address = withdraw_token_request_serializer.validated_data['to_address']
    logger.info(f'to_address:{to_address}')
    withdraw_amount = withdraw_token_request_serializer.validated_data['withdraw_amount']
    logger.info(f'withdraw_amount:{withdraw_amount}')
    success, account_balance, tx = TokenBalanceService.fetch_withdraw_update_user_hd_wallet_balance(
        token_id,user.id, int(withdraw_amount),to_address
    )
    withdraw_token_response_serializer = WithdrawTokenResponseSerializer(        {
    'to_address' : to_address,
    'withdraw_amount' : withdraw_amount,
    'token_id' : token_id,
    'free_amount' : str(account_balance.free_amount),
    'tx' : tx
    })
    logger.info(f'withdraw_token_response_serializer:{withdraw_token_response_serializer}')
    if(success):
        return Response(withdraw_token_response_serializer.data,status=200)
    else:    
        return Response(withdraw_token_response_serializer.data,status=400)
    

@swagger_auto_schema(
    method='post',
    manual_parameters=[token_id_param],
    request_body = ChargeTokenRequestSerializer,
    responses={200: ChargeTokenResponseSerializer}
)
@api_view(['post'])
@permission_classes([IsAuthenticated])
def charge_token(request):
    logger.info(f'request:{request}')
    user = request.user
    logger.info(f'user:{user}')
    token_id = request.query_params.get("token_id")
    logger.info(f'token_id:{token_id}')
    charge_token_request_serializer = ChargeTokenRequestSerializer(data=request.data)

    if not charge_token_request_serializer.is_valid():
        logger.error("invalid body")
        return Response(charge_token_request_serializer.errors, status=400)

    logger.info(f'charge_token_request_serializer: {charge_token_request_serializer}')
    charge_amount = charge_token_request_serializer.validated_data['charge_amount']
    logger.info(f'charge_amount:{charge_amount}')
    success, account_balance, tx = TokenBalanceService.transfer_from_user_to_central_hd_wallet_to_central_wallet(
        token_id,user.id, int(charge_amount)
    )
    charge_token_response_serializer = ChargeTokenResponseSerializer({
    'charged_amount' : charge_amount,
    'token_id' : token_id,
    'free_amount' : str(account_balance.free_amount),
    'tx' : tx
    })
    logger.info(f'withdraw_token_response_serializer:{charge_token_response_serializer}')
    if(success):
        return Response(charge_token_response_serializer.data,status=200)
    else:    
        return Response(charge_token_response_serializer.data,status=400)
    
