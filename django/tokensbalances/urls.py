
from django.urls import path

from . import views
urlpatterns = [
    path('tokens/', views.get_all_tokens)
]