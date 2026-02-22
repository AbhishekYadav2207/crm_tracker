from django.urls import path
from .views import PublicCHCSearchView, CHCListCreateView, CHCDetailView, AssignAdminView

urlpatterns = [
    path('public/search/', PublicCHCSearchView.as_view(), name='public-chc-search'),
    path('', CHCListCreateView.as_view(), name='chc-list-create'),
    path('<int:pk>/', CHCDetailView.as_view(), name='chc-detail'),
    path('<int:pk>/assign_admin/', AssignAdminView.as_view(), name='chc-assign-admin'),
]
