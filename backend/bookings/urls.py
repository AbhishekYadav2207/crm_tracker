from django.urls import path
from .views import PublicBookingCreateView, PublicBookingStatusView, CHCBookingListView, CHCBookingActionView

urlpatterns = [
    path('public/create/', PublicBookingCreateView.as_view(), name='public-booking-create'),
    path('public/<int:booking_id>/status/', PublicBookingStatusView.as_view(), name='public-booking-status'),
    path('chc/', CHCBookingListView.as_view(), name='chc-booking-list'),
    path('chc/<int:pk>/action/', CHCBookingActionView.as_view(), name='chc-booking-action'),
]
