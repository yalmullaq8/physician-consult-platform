from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from physicians.models import PhysicianProfile
from payments.services import PaymentServiceError, initiate_myfatoorah_payment

from .models import Booking
from .serializers import BookingCreateSerializer, BookingSerializer
from .services import BookingValidationError, create_pending_booking


class CreateBookingView(APIView):
	permission_classes = [permissions.AllowAny]

	def _get_requesting_user(self, request, requester_name: str, requester_email: str, requester_whatsapp_number: str):
		if request.user and request.user.is_authenticated:
			return request.user

		guest_user, _ = User.objects.get_or_create(
			email=requester_email,
			defaults={
				"full_name": requester_name,
				"phone_number": requester_whatsapp_number,
				"is_active": True,
			},
		)
		return guest_user

	def post(self, request):
		serializer = BookingCreateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		consulting_physician_id = serializer.validated_data["consulting_physician_id"]
		scheduled_start = serializer.validated_data["scheduled_start"]
		case_summary = serializer.validated_data["case_summary"]
		requester_name = serializer.validated_data["requester_name"]
		requester_specialization = serializer.validated_data["requester_specialization"]
		requester_country_of_practice = serializer.validated_data["requester_country_of_practice"]
		requester_email = serializer.validated_data["requester_email"]
		requester_whatsapp_number = serializer.validated_data.get("requester_whatsapp_number", "")
		payment_method_id = serializer.validated_data.get("payment_method_id")

		try:
			consulting_profile = PhysicianProfile.objects.get(pk=consulting_physician_id)
		except PhysicianProfile.DoesNotExist:
			return Response(
				{
					"success": False,
					"error": {
						"code": "booking_not_found",
						"message": "Consulting physician not found.",
					},
				},
				status=status.HTTP_404_NOT_FOUND,
			)

		try:
			requesting_user = self._get_requesting_user(
				request,
				requester_name=requester_name,
				requester_email=requester_email,
				requester_whatsapp_number=requester_whatsapp_number,
			)
			booking = create_pending_booking(
				requesting_user=requesting_user,
				consulting_physician_profile=consulting_profile,
				scheduled_start=scheduled_start,
				case_summary=case_summary,
				requester_name=requester_name,
				requester_specialization=requester_specialization,
				requester_country_of_practice=requester_country_of_practice,
				requester_email=requester_email,
				requester_whatsapp_number=requester_whatsapp_number,
			)
		except BookingValidationError as exc:
			return Response(
				{
					"success": False,
					"error": {
						"code": exc.code,
						"message": exc.message,
					},
				},
				status=status.HTTP_400_BAD_REQUEST,
			)

		try:
			_, payment_url = initiate_myfatoorah_payment(
				booking,
				payment_method_id=payment_method_id,
			)
		except PaymentServiceError as exc:
			return Response(
				{
					"success": False,
					"error": {
						"code": exc.code,
						"message": exc.message,
					},
				},
				status=status.HTTP_503_SERVICE_UNAVAILABLE,
			)

		return Response(
			{
				"success": True,
				"data": {
					"booking_reference": booking.booking_reference,
					"payment_url": payment_url,
				},
			},
			status=status.HTTP_201_CREATED,
		)


class BookingDetailView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request, booking_reference):
		booking = Booking.objects.filter(booking_reference=booking_reference).first()
		if not booking:
			return Response(
				{
					"success": False,
					"error": {
						"code": "booking_not_found",
						"message": "Booking not found.",
					},
				},
				status=status.HTTP_404_NOT_FOUND,
			)

		if request.user.id not in {booking.requesting_physician_id, booking.consulting_physician_id}:
			return Response(
				{
					"success": False,
					"error": {
						"code": "permission_denied",
						"message": "You do not have permission to view this booking.",
					},
				},
				status=status.HTTP_403_FORBIDDEN,
			)

		return Response({"success": True, "data": BookingSerializer(booking).data})


class MyBookingsView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		bookings = Booking.objects.filter(
			Q(requesting_physician=request.user) | Q(consulting_physician=request.user)
		).order_by("-scheduled_start")

		return Response({"success": True, "data": BookingSerializer(bookings, many=True).data})
