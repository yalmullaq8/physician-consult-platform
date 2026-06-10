from django.db import models
from django.utils import timezone


class Payment(models.Model):
	PROVIDER_MYFATOORAH = "myfatoorah"
	PROVIDER_CHOICES = ((PROVIDER_MYFATOORAH, "MyFatoorah"),)

	STATUS_INITIATED = "initiated"
	STATUS_PENDING = "pending"
	STATUS_PAID = "paid"
	STATUS_FAILED = "failed"
	STATUS_CANCELLED = "cancelled"
	STATUS_REFUNDED = "refunded"

	STATUS_CHOICES = (
		(STATUS_INITIATED, "Initiated"),
		(STATUS_PENDING, "Pending"),
		(STATUS_PAID, "Paid"),
		(STATUS_FAILED, "Failed"),
		(STATUS_CANCELLED, "Cancelled"),
		(STATUS_REFUNDED, "Refunded"),
	)

	booking = models.OneToOneField("bookings.Booking", on_delete=models.CASCADE, related_name="payment")
	provider = models.CharField(max_length=30, choices=PROVIDER_CHOICES, default=PROVIDER_MYFATOORAH)
	provider_invoice_id = models.CharField(max_length=120, blank=True)
	provider_payment_id = models.CharField(max_length=120, blank=True)
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	currency = models.CharField(max_length=10, default="USD")
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_INITIATED)
	raw_request = models.JSONField(default=dict, blank=True)
	raw_response = models.JSONField(default=dict, blank=True)
	paid_at = models.DateTimeField(null=True, blank=True)
	failed_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["provider", "provider_invoice_id"]),
			models.Index(fields=["provider", "provider_payment_id"]),
		]

	def mark_paid(self):
		self.status = self.STATUS_PAID
		self.paid_at = timezone.now()
		self.failed_at = None

	def __str__(self):
		return f"{self.provider}:{self.booking.booking_reference} ({self.status})"
