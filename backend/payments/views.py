from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponseRedirect
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import (
	PaymentServiceError,
	confirm_myfatoorah_payment,
	handle_myfatoorah_webhook,
	list_myfatoorah_payment_methods,
)


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
		payment_id = (
			request.query_params.get("paymentId")
			or request.query_params.get("PaymentId")
			or request.query_params.get("invoiceId")
			or request.query_params.get("InvoiceId")
			or request.query_params.get("Id")
		)
		base_url = settings.FRONTEND_BASE_URL.rstrip("/")

		if not payment_id:
			query = urlencode({"error": "Missing payment identifier in callback."})
			return HttpResponseRedirect(f"{base_url}/payment/error?{query}")

		try:
			confirm_myfatoorah_payment(payment_id)
		except PaymentServiceError as exc:
			query = urlencode({
				"paymentId": payment_id,
				"code": exc.code,
				"error": exc.message,
			})
			return HttpResponseRedirect(f"{base_url}/payment/error?{query}")

		query = urlencode({"paymentId": payment_id})
		return HttpResponseRedirect(f"{base_url}/payment/success?{query}")


class MyFatoorahConfirmView(APIView):
	permission_classes = [permissions.AllowAny]

	def get(self, request):
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
			payment = confirm_myfatoorah_payment(payment_id)
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
