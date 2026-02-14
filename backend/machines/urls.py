from django.urls import path
from .views import PublicMachineListView, DetailedMachineView, CHCMachineListCreateView, CHCMachineDetailView

urlpatterns = [
    path('public/', PublicMachineListView.as_view(), name='public-machine-list'),
    path('public/<int:pk>/', DetailedMachineView.as_view(), name='public-machine-detail'),
    path('', CHCMachineListCreateView.as_view(), name='chc-machine-list-create'),
    path('<int:pk>/', CHCMachineDetailView.as_view(), name='chc-machine-detail'),
]
