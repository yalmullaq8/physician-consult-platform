from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class Booking(models.Model):
	STATUS_DRAFT = "draft"
	STATUS_PENDING_PAYMENT = "pending_payment"
	STATUS_CONFIRMED = "confirmed"
	STATUS_COMPLETED = "completed"
	STATUS_CANCELLED = "cancelled"
	STATUS_NO_SHOW = "no_show"
	STATUS_REFUNDED = "refunded"

	STATUS_CHOICES = (
		(STATUS_DRAFT, "Draft"),
		(STATUS_PENDING_PAYMENT, "Pending payment"),
		(STATUS_CONFIRMED, "Confirmed"),
		(STATUS_COMPLETED, "Completed"),
		(STATUS_CANCELLED, "Cancelled"),
		(STATUS_NO_SHOW, "No show"),
		(STATUS_REFUNDED, "Refunded"),
	)

	booking_reference = models.CharField(max_length=32, unique=True)
	requesting_physician = models.ForeignKey(
		"accounts.User",
		on_delete=models.CASCADE,
		related_name="requested_bookings",
	)
	consulting_physician = models.ForeignKey(
		"accounts.User",
		on_delete=models.CASCADE,
		related_name="consulting_bookings",
	)
	scheduled_start = models.DateTimeField()
	scheduled_end = models.DateTimeField()
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING_PAYMENT)
	case_summary = models.TextField()
	meeting_url = models.URLField(blank=True)
	cancellation_reason = models.TextField(blank=True)
	cancelled_by = models.ForeignKey(
		"accounts.User",
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="cancelled_bookings",
	)
	cancelled_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-scheduled_start"]
		indexes = [
			models.Index(fields=["consulting_physician", "scheduled_start"]),
			models.Index(fields=["booking_reference"]),
		]

	def clean(self):
		if self.scheduled_start >= self.scheduled_end:
			raise ValidationError("Scheduled end must be later than scheduled start.")

		if self.scheduled_start <= timezone.now():
			raise ValidationError("Bookings must be scheduled in the future.")

	def save(self, *args, **kwargs):
		self.full_clean()
		super().save(*args, **kwargs)

	def __str__(self):
		return f"{self.booking_reference} - {self.consulting_physician.email}"
