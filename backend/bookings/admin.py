from django.contrib import admin
from django.utils import timezone

from audit.services import log_audit_event

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
	list_display = (
		"booking_reference",
		"requesting_physician",
		"consulting_physician",
		"scheduled_start",
		"status",
		"created_at",
	)
	list_filter = ("status", "scheduled_start")
	search_fields = (
		"booking_reference",
		"requesting_physician__email",
		"consulting_physician__email",
	)
	readonly_fields = ("created_at", "updated_at")
	actions = ("mark_completed", "mark_no_show", "cancel_bookings")

	def save_model(self, request, obj, form, change):
		action = "booking_updated" if change else "booking_created"
		super().save_model(request, obj, form, change)
		log_audit_event(
			actor=request.user,
			action=action,
			obj=obj,
			metadata={"changed_fields": form.changed_data if change else []},
		)

	def _log_bulk_action(self, request, queryset, action, metadata=None):
		selected_ids = list(queryset.values_list("id", flat=True))
		log_audit_event(
			actor=request.user,
			action=action,
			object_type="bookings.Booking",
			object_id="bulk",
			metadata={
				"ids": selected_ids,
				"count": len(selected_ids),
				**(metadata or {}),
			},
		)

	@admin.action(description="Mark selected bookings as completed")
	def mark_completed(self, request, queryset):
		updated = queryset.exclude(status=Booking.STATUS_COMPLETED).update(
			status=Booking.STATUS_COMPLETED,
			updated_at=timezone.now(),
		)
		self._log_bulk_action(request, queryset, "booking_admin_mark_completed", {"updated": updated})

	@admin.action(description="Mark selected bookings as no-show")
	def mark_no_show(self, request, queryset):
		updated = queryset.exclude(status=Booking.STATUS_NO_SHOW).update(
			status=Booking.STATUS_NO_SHOW,
			updated_at=timezone.now(),
		)
		self._log_bulk_action(request, queryset, "booking_admin_mark_no_show", {"updated": updated})

	@admin.action(description="Cancel selected bookings")
	def cancel_bookings(self, request, queryset):
		now = timezone.now()
		updated = queryset.exclude(status=Booking.STATUS_CANCELLED).update(
			status=Booking.STATUS_CANCELLED,
			cancellation_reason="Cancelled by admin",
			cancelled_by=request.user,
			cancelled_at=now,
			updated_at=now,
		)
		self._log_bulk_action(request, queryset, "booking_admin_cancelled", {"updated": updated})
