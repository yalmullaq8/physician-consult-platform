import csv
from datetime import datetime, time

from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogPagination(PageNumberPagination):
	page_size = 20
	page_size_query_param = "page_size"
	max_page_size = 100


def _parse_boundary(value, *, is_end=False):
	dt_value = parse_datetime(value)
	if dt_value is not None:
		if timezone.is_naive(dt_value):
			return timezone.make_aware(dt_value, timezone.get_current_timezone())
		return dt_value

	date_value = parse_date(value)
	if date_value is not None:
		boundary_time = time.max if is_end else time.min
		combined = datetime.combine(date_value, boundary_time)
		return timezone.make_aware(combined, timezone.get_current_timezone())

	return None


def _apply_common_filters(request, queryset):
	action = request.query_params.get("action")
	if action:
		queryset = queryset.filter(action=action)

	object_type = request.query_params.get("object_type")
	if object_type:
		queryset = queryset.filter(object_type=object_type)

	object_id = request.query_params.get("object_id")
	if object_id:
		queryset = queryset.filter(object_id=object_id)

	actor_email = request.query_params.get("actor_email")
	if actor_email:
		queryset = queryset.filter(actor__email__icontains=actor_email)

	created_from = request.query_params.get("created_from")
	if created_from:
		from_boundary = _parse_boundary(created_from, is_end=False)
		if from_boundary is None:
			return AuditLog.objects.none(), "created_from must be a valid ISO date or datetime."
		queryset = queryset.filter(created_at__gte=from_boundary)

	created_to = request.query_params.get("created_to")
	if created_to:
		to_boundary = _parse_boundary(created_to, is_end=True)
		if to_boundary is None:
			return AuditLog.objects.none(), "created_to must be a valid ISO date or datetime."
		queryset = queryset.filter(created_at__lte=to_boundary)

	return queryset, None


class AuditLogListView(generics.ListAPIView):
	permission_classes = [permissions.IsAdminUser]
	serializer_class = AuditLogSerializer
	pagination_class = AuditLogPagination
	date_filter_error = None

	def get_queryset(self):
		queryset = AuditLog.objects.select_related("actor").all()
		queryset, self.date_filter_error = _apply_common_filters(self.request, queryset)
		return queryset

	def list(self, request, *args, **kwargs):
		self.get_queryset()
		if self.date_filter_error:
			return Response(
				{
					"success": False,
					"error": {
						"code": "invalid_date_filter",
						"message": self.date_filter_error,
					},
				},
				status=status.HTTP_400_BAD_REQUEST,
			)

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


class AuditLogCSVExportView(APIView):
	permission_classes = [permissions.IsAdminUser]

	def get(self, request):
		queryset = AuditLog.objects.select_related("actor").all()
		queryset, filter_error = _apply_common_filters(request, queryset)
		if filter_error:
			return Response(
				{
					"success": False,
					"error": {
						"code": "invalid_date_filter",
						"message": filter_error,
					},
				},
				status=status.HTTP_400_BAD_REQUEST,
			)

		response = HttpResponse(content_type="text/csv")
		response["Content-Disposition"] = 'attachment; filename="audit_logs.csv"'

		writer = csv.writer(response)
		writer.writerow(["id", "created_at", "actor_email", "action", "object_type", "object_id", "metadata"])

		for log in queryset.iterator():
			writer.writerow(
				[
					log.id,
					log.created_at.isoformat(),
					log.actor.email if log.actor else "",
					log.action,
					log.object_type,
					log.object_id,
					log.metadata,
				]
			)

		return response
