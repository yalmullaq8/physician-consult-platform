from django.urls import path

from .views import (
    MyAvailabilityBlockCreateView,
    MyAvailabilityBlockDeleteView,
    MyAvailabilityExceptionCreateView,
    MyAvailabilityExceptionDeleteView,
    MyAvailabilityView,
    PublicPhysicianAvailableSlotsView,
    PublicPhysicianDetailView,
    PublicPhysicianListView,
    PublicSpecialtyListView,
)

urlpatterns = [
    path("physicians/", PublicPhysicianListView.as_view(), name="public-physician-list"),
    path("physicians/<slug:slug>/", PublicPhysicianDetailView.as_view(), name="public-physician-detail"),
    path(
        "physicians/<slug:slug>/available-slots/",
        PublicPhysicianAvailableSlotsView.as_view(),
        name="public-physician-available-slots",
    ),
    path("specialties/", PublicSpecialtyListView.as_view(), name="public-specialty-list"),
    path("me/availability/", MyAvailabilityView.as_view(), name="my-availability"),
    path("me/availability/blocks/", MyAvailabilityBlockCreateView.as_view(), name="my-availability-block-create"),
    path(
        "me/availability/blocks/<int:block_id>/",
        MyAvailabilityBlockDeleteView.as_view(),
        name="my-availability-block-delete",
    ),
    path(
        "me/availability/exceptions/",
        MyAvailabilityExceptionCreateView.as_view(),
        name="my-availability-exception-create",
    ),
    path(
        "me/availability/exceptions/<int:exception_id>/",
        MyAvailabilityExceptionDeleteView.as_view(),
        name="my-availability-exception-delete",
    ),
]