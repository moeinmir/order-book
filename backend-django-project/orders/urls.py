
from django.urls import path

from . import views
urlpatterns = [
    path('tokenpairs/', views.get_all_token_pairs),
    path('addorder/', views.add_order_for_me),
    path('orders/',views.get_all_orders)
]