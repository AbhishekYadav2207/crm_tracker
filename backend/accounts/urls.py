from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, MyTokenObtainPairView, UserProfileView, RegisterCHCAdminView, ChangePasswordView, CHCAdminListView, RemoveCHCAdminView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('register_chc_admin/', RegisterCHCAdminView.as_view(), name='register_chc_admin'),
    path('change_password/', ChangePasswordView.as_view(), name='change_password'),
    path('admins/', CHCAdminListView.as_view(), name='chc_admin_list'),
    path('remove_chc_admin/<int:pk>/', RemoveCHCAdminView.as_view(), name='remove_chc_admin'),
]
