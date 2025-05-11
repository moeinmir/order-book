from django.shortcuts import render

# Create your views here.

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterRequestSerializer
from .serializers import RegisterResponseSerializer

from rest_framework.permissions import IsAuthenticated

from rest_framework.permissions import IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from bip_utils import Bip44Changes
from .services import UserService

from rest_framework.decorators import api_view



@swagger_auto_schema(
    method='post',
    request_body=RegisterRequestSerializer,
    responses={201: RegisterResponseSerializer}
)
@api_view(['POST'])
def register(request):
    register_serializer_request = RegisterRequestSerializer(data=request.data)
    if register_serializer_request.is_valid():
        user = UserService.create_user(register_serializer_request.validated_data)
        register_response_serializer = RegisterResponseSerializer(user)
        return Response({"message": "User registered", "user":register_response_serializer.data }, status=status.HTTP_201_CREATED)
    return Response(register_serializer_request.errors, status=status.HTTP_400_BAD_REQUEST)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "eth_address": user.eth_address
        })
    


# class AdminOnlyView(APIView):
#     permission_classes = [IsAdminUser]

#     def get(self, request):
#         return Response({"message": "You are an admin!"})



from web3 import Web3
from django.conf import settings

w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URI))

def get_eth_balance(address: str) -> float:
    # Ensure checksum address
    checksum_address = w3.to_checksum_address(address)
    # Get balance in wei
    balance_wei = w3.eth.get_balance(checksum_address)
    # Convert to Ether
    return w3.from_wei(balance_wei, 'ether')


from rest_framework.views import APIView
from rest_framework.response import Response
from .models import CustomUser


class UserBalanceView(APIView):
    def get(self, request):
        user = CustomUser.objects.get(id=3)
        eth_address = user.eth_address
        balance = get_eth_balance(eth_address)
        return Response({"user_id": user.id, "eth_address": eth_address, "balance": str(balance)})


from web3 import Web3
from django.conf import settings
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins

w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URI))

def load_private_key_from_index(index: int) -> str:
    mnemonic = settings.APP_MNEMONIC
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()

    bip44 = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
    account = bip44.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(index)
    return account.PrivateKey().Raw().ToHex()

def send_eth(from_index: int, to_address: str, amount_eth: float) -> str:
    private_key = load_private_key_from_index(from_index)
    from_account = w3.eth.account.from_key(private_key)
    to_address = w3.to_checksum_address(to_address)

    nonce = w3.eth.get_transaction_count(from_account.address)
    gas_price = w3.eth.gas_price
    value = w3.to_wei(amount_eth, 'ether')

    tx = {
        'nonce': nonce,
        'to': to_address,
        'value': value,
        'gas': 21000,
        'gasPrice': gas_price,
        'chainId': 11155111  # Sepolia chain ID
    }

    signed_tx = from_account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    return tx_hash.hex()


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CustomUser

class SendEthView(APIView):
    def post(self, request):
        to_address = request.data.get("to")
        if not to_address:
            return Response({"error": "Missing 'to' address"}, status=400)

        try:
            tx_hash = send_eth(from_index=CustomUser.objects.get(id=3).eth_index, to_address=to_address, amount_eth=0.0005)
            return Response({"tx_hash": tx_hash})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "success", "type": "bool"}],
        "type": "function",
    },
]


from web3 import Web3

# Sepolia RPC URL from Infura/Alchemy or local node
w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URI))

def get_token_contract(token_address: str):
    return w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)


def get_user_token_balance(user_eth_address: str, token_address: str) -> int:
    contract = get_token_contract(token_address)
    balance = contract.functions.balanceOf(Web3.to_checksum_address(user_eth_address)).call()
    return balance

user = CustomUser.objects.get(id=3)
balance = get_user_token_balance(user.eth_address, "0x216cb9acB601474b2b27ee0BbaFc94c1C7148577")


def transfer_token_from_user(user, to_address: str, amount: int, token_address: str) -> str:
    # Get private key and sender address
    keys = derive_eth_address(user.eth_index)
    private_key = keys['private_key']
    from_address = Web3.to_checksum_address(user.eth_address)
    to_address = Web3.to_checksum_address(to_address)

    contract = get_token_contract(token_address)

    # Build transaction
    nonce = w3.eth.get_transaction_count(from_address)
    tx = contract.functions.transfer(to_address, amount).build_transaction({
        'chainId': 11155111,  # Sepolia
        'gas': 100000,
        'gasPrice': w3.eth.gas_price,
        'nonce': nonce
    })

    # Sign and send
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    return tx_hash.hex()

from rest_framework.decorators import api_view
from rest_framework.response import Response

def derive_eth_address(user_index: int) -> dict:
    mnemonic = settings.APP_MNEMONIC
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
    bip44_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
    
    bip44_acc = (
        bip44_mst
        .Purpose()
        .Coin()
        .Account(0)
        .Change(Bip44Changes.CHAIN_EXT) 
        .AddressIndex(user_index)
    )
    return {
        "address": bip44_acc.PublicKey().ToAddress(), 
        "private_key": bip44_acc.PrivateKey().Raw().ToHex()
    }


@api_view(['POST'])
def send_token(request):
    user = CustomUser.objects.get(id=3)
    to = request.data.get("to")
    amount = int(request.data.get("amount"))  # In smallest unit, e.g., wei
    token = request.data.get("token")

    tx = transfer_token_from_user(user, to, amount, token)
    return Response({"tx_hash": tx})


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import CustomUser


@api_view(['GET'])
def get_token_balance(request, user_id):
    token_address = request.query_params.get("token")
    print("token address")
    if not token_address:
        return Response({"error": "token address required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = CustomUser.objects.get(id=user_id)
        print("user")
        print(user)
        balance = get_user_token_balance(user.eth_address, token_address)
        print("balance")
        print(balance)
        return Response({"balance": str(balance), "eth_address": user.eth_address})
    except CustomUser.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
