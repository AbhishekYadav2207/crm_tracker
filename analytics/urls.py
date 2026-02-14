from django.urls import path
from .views import GovtDashboardView, CHCDashboardView, MachineAnalyticsView

urlpatterns = [
    path('govt/dashboard/', GovtDashboardView.as_view(), name='govt-dashboard'),
    path('chc/dashboard/', CHCDashboardView.as_view(), name='chc-dashboard'),
    path('machines/', MachineAnalyticsView.as_view(), name='machine-analytics'),
]
