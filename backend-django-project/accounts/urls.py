from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# from .views import UserBalanceView
# from .views import SendEthView
from . import views
urlpatterns = [
    path('register/', views.register),
    path('my-account',views.my_account_information),
    path('token/', TokenObtainPairView.as_view()),     
    path('token/refresh/', TokenRefreshView.as_view()),    
    # # path('me/', MeView.as_view()),                          # current user
    # # path('admin-only/', AdminOnlyView.as_view()),           # permission-based
    # path('balance/', UserBalanceView.as_view(),),
    # path('send-eth/', SendEthView.as_view(),),

    # path('token-balance/<int:user_id>/', views.get_token_balance,),
    # path('token-transfer/', views.send_token, name='send_token'),
    
]

   