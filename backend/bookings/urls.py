from django.urls import path

from .views import BookingDetailView, CreateBookingView, MyBookingsView

urlpatterns = [
    path("bookings/", CreateBookingView.as_view(), name="create-booking"),
    path("bookings/<str:booking_reference>/", BookingDetailView.as_view(), name="booking-detail"),
    path("me/bookings/", MyBookingsView.as_view(), name="my-bookings"),
]
