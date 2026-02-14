from django.urls import path
from .views import PublicCHCSearchView, CHCListCreateView, CHCDetailView

urlpatterns = [
    path('public/search/', PublicCHCSearchView.as_view(), name='public-chc-search'),
    path('', CHCListCreateView.as_view(), name='chc-list-create'),
    path('<int:pk>/', CHCDetailView.as_view(), name='chc-detail'),
]
