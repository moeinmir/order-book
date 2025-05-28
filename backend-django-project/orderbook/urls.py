from django.contrib import admin
from django.urls import path, include
from django.urls import path, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),  
    path('api/tokensbalances/',include('tokensbalances.urls')),  
    path('api/orders/',include('orders.urls'))  
    
]

schema_view = get_schema_view(
    openapi.Info(
        title="Order Book",
        default_version='v1',
        description="API Documentation for Crypto Order Book",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns += [
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

