from django.urls import path
from .views import MachineUsageListCreateView

urlpatterns = [
    path('', MachineUsageListCreateView.as_view(), name='usage-list-create'),
]
