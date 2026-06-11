from urllib.parse import urlencode
import logging

from django.conf import settings
from django.http import HttpResponseRedirect
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import (
	PaymentServiceError,
	confirm_myfatoorah_payment,
	get_local_myfatoorah_payment,
	handle_myfatoorah_webhook,
	list_myfatoorah_payment_methods,
)


logger = logging.getLogger(__name__)


class MyFatoorahPaymentMethodsView(APIView):
	permission_classes = [permissions.AllowAny]

	def get(self, request):
		amount = request.query_params.get("amount", "1")
		try:
			invoice_amount = float(amount)
		except ValueError:
			return Response(
				{
					"success": False,
					"error": {
						"code": "payment_failed",
						"message": "Invalid amount query parameter.",
					},
				},
				status=status.HTTP_400_BAD_REQUEST,
			)

		if invoice_amount <= 0:
			invoice_amount = 1

		try:
			methods = list_myfatoorah_payment_methods(invoice_amount)
		except PaymentServiceError as exc:
			return Response(
				{
					"success": False,
					"error": {"code": exc.code, "message": exc.message},
				},
				status=status.HTTP_400_BAD_REQUEST,
			)

		return Response({"success": True, "data": methods})


class MyFatoorahCallbackView(APIView):
	permission_classes = [permissions.AllowAny]

	def get(self, request):
		booking_reference = (
			request.query_params.get("bookingReference")
			or request.query_params.get("booking_reference")
		)
		payment_id = (
			request.query_params.get("paymentId")
			or request.query_params.get("PaymentId")
			or request.query_params.get("invoiceId")
			or request.query_params.get("InvoiceId")
			or request.query_params.get("Id")
		)
		base_url = settings.FRONTEND_BASE_URL.rstrip("/")

		if not payment_id:
			return Response(
				{
					"success": True,
					"message": "Callback endpoint is reachable. Awaiting payment identifier.",
				},
				status=status.HTTP_200_OK,
			)

		query = {"paymentId": payment_id}
		if booking_reference:
			query["bookingReference"] = booking_reference
		return HttpResponseRedirect(f"{base_url}/payment/success?{urlencode(query)}")


class MyFatoorahConfirmView(APIView):
	permission_classes = [permissions.AllowAny]

	def get(self, request):
		booking_reference = (
			request.query_params.get("bookingReference")
			or request.query_params.get("booking_reference")
		)
		payment_id = (
			request.query_params.get("paymentId")
			or request.query_params.get("PaymentId")
			or request.query_params.get("invoiceId")
			or request.query_params.get("InvoiceId")
			or request.query_params.get("Id")
		)

		if not payment_id:
			return Response(
				{
					"success": False,
					"error": {"code": "payment_failed", "message": "Missing payment identifier in callback."},
				},
				status=status.HTTP_400_BAD_REQUEST,
			)

		try:
			payment = confirm_myfatoorah_payment(payment_id, booking_reference=booking_reference)
		except PaymentServiceError as exc:
			return Response(
				{
					"success": False,
					"error": {"code": exc.code, "message": exc.message},
				},
				status=status.HTTP_400_BAD_REQUEST,
			)
		except Exception:
			logger.exception(
				"Unexpected error in MyFatoorah confirm endpoint.",
				extra={"payment_id": payment_id, "booking_reference": booking_reference},
			)
			fallback_payment = get_local_myfatoorah_payment(payment_id, booking_reference=booking_reference)
			if fallback_payment:
				return Response(
					{
						"success": True,
						"data": {
							"booking_reference": fallback_payment.booking.booking_reference,
							"payment_status": fallback_payment.status,
							"booking_status": fallback_payment.booking.status,
						},
					}
				)
			return Response(
				{
					"success": False,
					"error": {
						"code": "payment_internal_error",
						"message": "Unexpected server error during payment confirmation.",
					},
				},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR,
			)

		return Response(
			{
				"success": True,
				"data": {
					"booking_reference": payment.booking.booking_reference,
					"payment_status": payment.status,
					"booking_status": payment.booking.status,
				},
			}
		)


class MyFatoorahErrorView(APIView):
	permission_classes = [permissions.AllowAny]

	def get(self, request):
		return Response(
			{
				"success": False,
				"error": {
					"code": "payment_failed",
					"message": "Payment was cancelled or failed. Please try again.",
				},
			},
			status=status.HTTP_400_BAD_REQUEST,
		)


class MyFatoorahWebhookView(APIView):
	permission_classes = [permissions.AllowAny]

	def post(self, request):
		try:
			payment = handle_myfatoorah_webhook(request.data)
		except PaymentServiceError as exc:
			return Response(
				{
					"success": False,
					"error": {"code": exc.code, "message": exc.message},
				},
				status=status.HTTP_400_BAD_REQUEST,
			)

		return Response(
			{
				"success": True,
				"data": {
					"booking_reference": payment.booking.booking_reference,
					"payment_status": payment.status,
				},
			}
		)
