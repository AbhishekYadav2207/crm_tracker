from django.urls import path
from .views import MachineUsageListCreateView, MachineUsageDetailView

urlpatterns = [
    path('', MachineUsageListCreateView.as_view(), name='usage-list-create'),
    path('<int:pk>/', MachineUsageDetailView.as_view(), name='usage-detail'),
]
