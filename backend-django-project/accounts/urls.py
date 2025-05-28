from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
urlpatterns = [
    path('register/', views.register),
    path('my-account',views.my_account_information),
    path('token/', TokenObtainPairView.as_view()),     
    path('token/refresh/', TokenRefreshView.as_view()),       
]

   