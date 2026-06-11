from django.urls import path

from .views import (
    MyFatoorahCallbackView,
    MyFatoorahConfirmView,
    MyFatoorahErrorView,
    MyFatoorahPaymentMethodsView,
    MyFatoorahWebhookView,
)

urlpatterns = [
    path("payments/myfatoorah/methods/", MyFatoorahPaymentMethodsView.as_view(), name="myfatoorah-methods"),
    path("payments/myfatoorah/confirm/", MyFatoorahConfirmView.as_view(), name="myfatoorah-confirm"),
    path("payments/myfatoorah/callback/", MyFatoorahCallbackView.as_view(), name="myfatoorah-callback"),
    path("payments/myfatoorah/error/", MyFatoorahErrorView.as_view(), name="myfatoorah-error"),
    path("payments/myfatoorah/webhook/", MyFatoorahWebhookView.as_view(), name="myfatoorah-webhook"),
]
