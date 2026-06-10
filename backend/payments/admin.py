from django.contrib import admin
from django.utils import timezone

from audit.services import log_audit_event
from bookings.models import Booking

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
	list_display = (
		"booking",
		"provider",
		"provider_invoice_id",
		"amount",
		"currency",
		"status",
		"paid_at",
		"created_at",
	)
	list_filter = ("provider", "status", "currency", "created_at")
	search_fields = ("provider_invoice_id", "provider_payment_id", "booking__booking_reference")
	readonly_fields = ("created_at", "updated_at")
	actions = ("mark_paid", "mark_failed", "mark_refunded")
	date_hierarchy = "created_at"
	list_select_related = ("booking",)

	def save_model(self, request, obj, form, change):
		action = "payment_updated" if change else "payment_created"
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
			object_type="payments.Payment",
			object_id="bulk",
			metadata={"ids": selected_ids, "count": len(selected_ids), **(metadata or {})},
		)

	@admin.action(description="Mark selected payments as paid")
	def mark_paid(self, request, queryset):
		now = timezone.now()
		updated = 0
		skipped = []

		for payment in queryset.select_related("booking"):
			if payment.status in {Payment.STATUS_PAID, Payment.STATUS_REFUNDED}:
				skipped.append(payment.id)
				continue

			Payment.objects.filter(pk=payment.pk).update(
				status=Payment.STATUS_PAID,
				paid_at=now,
				failed_at=None,
				updated_at=now,
			)

			if payment.booking.status in {
				Booking.STATUS_DRAFT,
				Booking.STATUS_PENDING_PAYMENT,
				Booking.STATUS_CANCELLED,
			}:
				Booking.objects.filter(pk=payment.booking_id).update(
					status=Booking.STATUS_CONFIRMED,
					updated_at=now,
				)
			updated += 1

		self._log_bulk_action(
			request,
			queryset,
			"payment_admin_mark_paid",
			{"updated": updated, "skipped": skipped},
		)

	@admin.action(description="Mark selected payments as failed")
	def mark_failed(self, request, queryset):
		now = timezone.now()
		updated = 0
		skipped = []

		for payment in queryset.select_related("booking"):
			if payment.status in {Payment.STATUS_PAID, Payment.STATUS_REFUNDED}:
				skipped.append(payment.id)
				continue

			Payment.objects.filter(pk=payment.pk).update(
				status=Payment.STATUS_FAILED,
				failed_at=now,
				updated_at=now,
			)

			if payment.booking.status == Booking.STATUS_PENDING_PAYMENT:
				Booking.objects.filter(pk=payment.booking_id).update(
					status=Booking.STATUS_CANCELLED,
					cancellation_reason="Cancelled after manual payment failure mark.",
					cancelled_by=request.user,
					cancelled_at=now,
					updated_at=now,
				)
			updated += 1

		self._log_bulk_action(
			request,
			queryset,
			"payment_admin_mark_failed",
			{"updated": updated, "skipped": skipped},
		)

	@admin.action(description="Mark selected payments as refunded")
	def mark_refunded(self, request, queryset):
		now = timezone.now()
		updated = 0
		skipped = []

		for payment in queryset.select_related("booking"):
			if payment.status != Payment.STATUS_PAID:
				skipped.append(payment.id)
				continue

			Payment.objects.filter(pk=payment.pk).update(
				status=Payment.STATUS_REFUNDED,
				updated_at=now,
			)
			Booking.objects.filter(pk=payment.booking_id).update(
				status=Booking.STATUS_REFUNDED,
				updated_at=now,
			)
			updated += 1

		self._log_bulk_action(
			request,
			queryset,
			"payment_admin_mark_refunded",
			{"updated": updated, "skipped": skipped},
		)
