from rest_framework.response import Response
from .serializers import RegisterRequestSerializer
from .serializers import RegisterResponseSerializer
from .serializers import GetUserAccountInformationSerializer
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from .services import UserService
from rest_framework.decorators import api_view, permission_classes

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
        return Response({"message": "User registered", "user":register_response_serializer.data }, status=200)
    return Response(register_serializer_request.errors, status=400)

@swagger_auto_schema(
    method='get',
    responses={200:GetUserAccountInformationSerializer }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_account_information(request):
    user = request.user
    response = GetUserAccountInformationSerializer(user)
    return Response({"message": "User Information", "user":response.data }, status=200)
