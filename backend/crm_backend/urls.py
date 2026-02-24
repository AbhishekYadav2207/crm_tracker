from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="CRM API",
      default_version='v1',
      description="API documentation for Crop Residue Management System",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@crm.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
   # Add this
   SWAGGER_SETTINGS = {
      'SECURITY_DEFINITIONS': {
         'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Enter: Bearer <access_token>',
         }
      }
   }
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Endpoints
    path('api/v1/auth/', include('accounts.urls')),
    path('api/v1/chc/', include('chc.urls')),
    path('api/v1/machines/', include('machines.urls')),
    path('api/v1/bookings/', include('bookings.urls')),
    path('api/v1/usage/', include('usage.urls')),
    path('api/v1/analytics/', include('analytics.urls')),

    # Swagger Documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
