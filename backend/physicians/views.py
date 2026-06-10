from datetime import date

from django.db.models import Q
from rest_framework import generics, permissions, serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.services import log_audit_event

from .models import PhysicianProfile, Specialty
from .services import generate_available_slots
from .serializers import (
	AvailabilityExceptionSerializer,
	PhysicianAvailabilitySerializer,
	PhysicianDetailSerializer,
	PhysicianListSerializer,
	SpecialtySerializer,
)


class APISuccessListMixin:
	def list(self, request, *args, **kwargs):
		response = super().list(request, *args, **kwargs)
		if isinstance(response.data, dict) and "results" in response.data:
			return Response(
				{
					"success": True,
					"data": {
						"count": response.data.get("count", 0),
						"next": response.data.get("next"),
						"previous": response.data.get("previous"),
						"results": response.data.get("results", []),
					},
				}
			)
		return Response({"success": True, "data": response.data})


class APISuccessRetrieveMixin:
	def retrieve(self, request, *args, **kwargs):
		response = super().retrieve(request, *args, **kwargs)
		return Response({"success": True, "data": response.data})


class PublicSpecialtyListView(APISuccessListMixin, generics.ListAPIView):
	permission_classes = [AllowAny]
	serializer_class = SpecialtySerializer

	def get_queryset(self):
		return Specialty.objects.filter(is_active=True).order_by("display_order", "name")


class PublicPhysicianListView(APISuccessListMixin, generics.ListAPIView):
	permission_classes = [AllowAny]
	serializer_class = PhysicianListSerializer

	def get_queryset(self):
		queryset = (
			PhysicianProfile.objects.select_related("specialty")
			.filter(is_verified=True, accepts_bookings=True, specialty__is_active=True)
			.order_by("full_name")
		)

		specialty_value = self.request.query_params.get("specialty")
		if specialty_value:
			if specialty_value.isdigit():
				queryset = queryset.filter(specialty_id=int(specialty_value))
			else:
				queryset = queryset.filter(specialty__slug=specialty_value)

		search_value = self.request.query_params.get("search")
		if search_value:
			queryset = queryset.filter(
				Q(full_name__icontains=search_value)
				| Q(user__email__icontains=search_value)
				| Q(specialty__name__icontains=search_value)
			)

		featured_value = self.request.query_params.get("featured")
		if featured_value is not None:
			featured = featured_value.lower() in {"1", "true", "yes"}
			queryset = queryset.filter(is_featured=featured)

		return queryset


class PublicPhysicianDetailView(APISuccessRetrieveMixin, generics.RetrieveAPIView):
	permission_classes = [AllowAny]
	serializer_class = PhysicianDetailSerializer
	lookup_field = "slug"

	def get_queryset(self):
		return PhysicianProfile.objects.select_related("specialty").filter(
			is_verified=True,
			accepts_bookings=True,
			specialty__is_active=True,
		)


class PublicPhysicianAvailableSlotsView(APIView):
	permission_classes = [AllowAny]

	def get(self, request, slug):
		requested_date = request.query_params.get("date")
		if not requested_date:
			return Response(
				{
					"success": False,
					"error": {
						"code": "slot_unavailable",
						"message": "date query parameter is required.",
					},
				},
				status=400,
			)

		try:
			target_date = date.fromisoformat(requested_date)
		except ValueError:
			return Response(
				{
					"success": False,
					"error": {
						"code": "slot_unavailable",
						"message": "date must be in YYYY-MM-DD format.",
					},
				},
				status=400,
			)

		physician = PhysicianProfile.objects.filter(
			slug=slug,
			is_verified=True,
			accepts_bookings=True,
			specialty__is_active=True,
		).first()

		if not physician:
			return Response(
				{
					"success": False,
					"error": {
						"code": "booking_not_found",
						"message": "Physician not found.",
					},
				},
				status=404,
			)

		slots = generate_available_slots(physician, target_date)
		serialized_slots = [{"start": start.isoformat(), "end": end.isoformat()} for start, end in slots]

		return Response(
			{
				"success": True,
				"data": {
					"date": target_date.isoformat(),
					"slots": serialized_slots,
				},
			}
		)


class MyAvailabilityView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def _get_physician_profile(self, request):
		profile = getattr(request.user, "physician_profile", None)
		if not profile:
			raise PermissionDenied("Only physician accounts can manage availability.")
		return profile

	def get(self, request):
		profile = self._get_physician_profile(request)
		availabilities = profile.availabilities.filter(is_active=True).order_by("weekday", "start_time")
		exceptions = profile.availability_exceptions.order_by("date", "start_time")

		return Response(
			{
				"success": True,
				"data": {
					"blocks": PhysicianAvailabilitySerializer(availabilities, many=True).data,
					"exceptions": AvailabilityExceptionSerializer(exceptions, many=True).data,
				},
			}
		)


class MyAvailabilityBlockCreateView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def _get_physician_profile(self, request):
		profile = getattr(request.user, "physician_profile", None)
		if not profile:
			raise PermissionDenied("Only physician accounts can manage availability.")
		return profile

	def post(self, request):
		profile = self._get_physician_profile(request)
		serializer = PhysicianAvailabilitySerializer(data=request.data)
		if not serializer.is_valid():
			return Response(
				{
					"success": False,
					"error": {
						"code": "availability_invalid",
						"message": serializer.errors,
					},
				},
				status=status.HTTP_400_BAD_REQUEST,
			)

		try:
			block = serializer.save(physician=profile)
		except serializers.ValidationError as exc:
			return Response(
				{
					"success": False,
					"error": {
						"code": "availability_invalid",
						"message": exc.detail,
					},
				},
				status=status.HTTP_400_BAD_REQUEST,
			)

		log_audit_event(actor=request.user, action="availability_block_created", obj=block)

		return Response(
			{"success": True, "data": PhysicianAvailabilitySerializer(block).data},
			status=status.HTTP_201_CREATED,
		)


class MyAvailabilityBlockDeleteView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def _get_physician_profile(self, request):
		profile = getattr(request.user, "physician_profile", None)
		if not profile:
			raise PermissionDenied("Only physician accounts can manage availability.")
		return profile

	def delete(self, request, block_id):
		profile = self._get_physician_profile(request)
		block = profile.availabilities.filter(pk=block_id).first()
		if not block:
			return Response(
				{
					"success": False,
					"error": {
						"code": "booking_not_found",
						"message": "Availability block not found.",
					},
				},
				status=status.HTTP_404_NOT_FOUND,
			)

		block_id_value = block.pk
		block.delete()
		log_audit_event(
			actor=request.user,
			action="availability_block_deleted",
			object_type="physicians.PhysicianAvailability",
			object_id=block_id_value,
		)

		return Response({"success": True, "data": {"id": block_id_value}})

	def patch(self, request, block_id):
		profile = self._get_physician_profile(request)
		block = profile.availabilities.filter(pk=block_id).first()
		if not block:
			return Response(
				{
					"success": False,
					"error": {
						"code": "booking_not_found",
						"message": "Availability block not found.",
					},
				},
				status=status.HTTP_404_NOT_FOUND,
			)

		serializer = PhysicianAvailabilitySerializer(block, data=request.data, partial=True)
		if not serializer.is_valid():
			return Response(
				{
					"success": False,
					"error": {
						"code": "availability_invalid",
						"message": serializer.errors,
					},
				},
				status=status.HTTP_400_BAD_REQUEST,
			)

		try:
			updated_block = serializer.save()
		except serializers.ValidationError as exc:
			return Response(
				{
					"success": False,
					"error": {
						"code": "availability_invalid",
						"message": exc.detail,
					},
				},
				status=status.HTTP_400_BAD_REQUEST,
			)

		log_audit_event(actor=request.user, action="availability_block_updated", obj=updated_block)
		return Response({"success": True, "data": PhysicianAvailabilitySerializer(updated_block).data})


class MyAvailabilityExceptionCreateView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def _get_physician_profile(self, request):
		profile = getattr(request.user, "physician_profile", None)
		if not profile:
			raise PermissionDenied("Only physician accounts can manage availability.")
		return profile

	def post(self, request):
		profile = self._get_physician_profile(request)
		serializer = AvailabilityExceptionSerializer(data=request.data)
		if not serializer.is_valid():
			return Response(
				{
					"success": False,
					"error": {
						"code": "availability_invalid",
						"message": serializer.errors,
					},
				},
				status=status.HTTP_400_BAD_REQUEST,
			)

		try:
			exception = serializer.save(physician=profile)
		except serializers.ValidationError as exc:
			return Response(
				{
					"success": False,
					"error": {
						"code": "availability_invalid",
						"message": exc.detail,
					},
				},
				status=status.HTTP_400_BAD_REQUEST,
			)

		log_audit_event(actor=request.user, action="availability_exception_created", obj=exception)

		return Response(
			{"success": True, "data": AvailabilityExceptionSerializer(exception).data},
			status=status.HTTP_201_CREATED,
		)


class MyAvailabilityExceptionDeleteView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def _get_physician_profile(self, request):
		profile = getattr(request.user, "physician_profile", None)
		if not profile:
			raise PermissionDenied("Only physician accounts can manage availability.")
		return profile

	def delete(self, request, exception_id):
		profile = self._get_physician_profile(request)
		exception = profile.availability_exceptions.filter(pk=exception_id).first()
		if not exception:
			return Response(
				{
					"success": False,
					"error": {
						"code": "booking_not_found",
						"message": "Availability exception not found.",
					},
				},
				status=status.HTTP_404_NOT_FOUND,
			)

		exception_id_value = exception.pk
		exception.delete()
		log_audit_event(
			actor=request.user,
			action="availability_exception_deleted",
			object_type="physicians.AvailabilityException",
			object_id=exception_id_value,
		)

		return Response({"success": True, "data": {"id": exception_id_value}})

	def patch(self, request, exception_id):
		profile = self._get_physician_profile(request)
		exception = profile.availability_exceptions.filter(pk=exception_id).first()
		if not exception:
			return Response(
				{
					"success": False,
					"error": {
						"code": "booking_not_found",
						"message": "Availability exception not found.",
					},
				},
				status=status.HTTP_404_NOT_FOUND,
			)

		serializer = AvailabilityExceptionSerializer(exception, data=request.data, partial=True)
		if not serializer.is_valid():
			return Response(
				{
					"success": False,
					"error": {
						"code": "availability_invalid",
						"message": serializer.errors,
					},
				},
				status=status.HTTP_400_BAD_REQUEST,
			)

		try:
			updated_exception = serializer.save()
		except serializers.ValidationError as exc:
			return Response(
				{
					"success": False,
					"error": {
						"code": "availability_invalid",
						"message": exc.detail,
					},
				},
				status=status.HTTP_400_BAD_REQUEST,
			)

		log_audit_event(actor=request.user, action="availability_exception_updated", obj=updated_exception)
		return Response({"success": True, "data": AvailabilityExceptionSerializer(updated_exception).data})
