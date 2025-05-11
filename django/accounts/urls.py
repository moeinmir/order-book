from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, MeView, AdminOnlyView
from .views import UserBalanceView
from .views import SendEthView
from . import views
urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('token/', TokenObtainPairView.as_view()),         # login, returns access + refresh
    path('token/refresh/', TokenRefreshView.as_view()),    # refresh access token
    path('me/', MeView.as_view()),                          # current user
    path('admin-only/', AdminOnlyView.as_view()),           # permission-based
    path('balance/', UserBalanceView.as_view(),),
    path('send-eth/', SendEthView.as_view(),),

    path('token-balance/<int:user_id>/', views.get_token_balance,),
    path('token-transfer/', views.send_token, name='send_token'),
]

   