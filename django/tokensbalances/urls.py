
from django.urls import path

from . import views
urlpatterns = [
    path('tokens/', views.get_all_tokens),
    path('getmytokenbalance/',views.get_my_token_balance),
    path('withdrawtoken/',views.withdraw_token)   
]