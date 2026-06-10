from django.contrib import admin
from django.utils import timezone

from audit.services import log_audit_event

from .models import NotificationLog


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
	list_display = (
		"notification_type",
		"recipient",
		"channel",
		"status",
		"booking",
		"sent_at",
		"created_at",
	)
	list_filter = ("notification_type", "channel", "status", "created_at")
	search_fields = ("recipient__email", "booking__booking_reference", "dedupe_key")
	readonly_fields = ("created_at", "updated_at")
	actions = ("mark_sent", "mark_failed", "reset_to_pending")
	date_hierarchy = "created_at"
	list_select_related = ("recipient", "booking")

	def save_model(self, request, obj, form, change):
		action = "notification_log_updated" if change else "notification_log_created"
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
			object_type="notifications.NotificationLog",
			object_id="bulk",
			metadata={"ids": selected_ids, "count": len(selected_ids), **(metadata or {})},
		)

	@admin.action(description="Mark selected notifications as sent")
	def mark_sent(self, request, queryset):
		now = timezone.now()
		updated = queryset.exclude(status=NotificationLog.STATUS_SENT).update(
			status=NotificationLog.STATUS_SENT,
			sent_at=now,
			failed_at=None,
			updated_at=now,
		)
		self._log_bulk_action(request, queryset, "notification_admin_mark_sent", {"updated": updated})

	@admin.action(description="Mark selected notifications as failed")
	def mark_failed(self, request, queryset):
		now = timezone.now()
		updated = queryset.exclude(status=NotificationLog.STATUS_FAILED).update(
			status=NotificationLog.STATUS_FAILED,
			failed_at=now,
			updated_at=now,
		)
		self._log_bulk_action(request, queryset, "notification_admin_mark_failed", {"updated": updated})

	@admin.action(description="Reset selected notifications to pending")
	def reset_to_pending(self, request, queryset):
		now = timezone.now()
		updated = queryset.exclude(status=NotificationLog.STATUS_PENDING).update(
			status=NotificationLog.STATUS_PENDING,
			sent_at=None,
			failed_at=None,
			updated_at=now,
		)
		self._log_bulk_action(request, queryset, "notification_admin_reset_pending", {"updated": updated})
