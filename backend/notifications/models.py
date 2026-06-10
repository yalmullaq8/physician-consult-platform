from django.db import models


class NotificationLog(models.Model):
	TYPE_BOOKING_CONFIRMED_REQUESTER = "booking_confirmed_requester"
	TYPE_BOOKING_CONFIRMED_CONSULTANT = "booking_confirmed_consultant"
	TYPE_BOOKING_REMINDER_24H = "booking_reminder_24h"
	TYPE_BOOKING_REMINDER_1H = "booking_reminder_1h"
	TYPE_PAYMENT_FAILED = "payment_failed"

	NOTIFICATION_TYPE_CHOICES = (
		(TYPE_BOOKING_CONFIRMED_REQUESTER, "Booking confirmed - requesting physician"),
		(TYPE_BOOKING_CONFIRMED_CONSULTANT, "Booking confirmed - consulting physician"),
		(TYPE_BOOKING_REMINDER_24H, "Consultation reminder - 24h"),
		(TYPE_BOOKING_REMINDER_1H, "Consultation reminder - 1h"),
		(TYPE_PAYMENT_FAILED, "Payment failed"),
	)

	CHANNEL_EMAIL = "email"
	CHANNEL_CHOICES = ((CHANNEL_EMAIL, "Email"),)

	STATUS_PENDING = "pending"
	STATUS_SENT = "sent"
	STATUS_FAILED = "failed"
	STATUS_CHOICES = (
		(STATUS_PENDING, "Pending"),
		(STATUS_SENT, "Sent"),
		(STATUS_FAILED, "Failed"),
	)

	recipient = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="notification_logs")
	booking = models.ForeignKey(
		"bookings.Booking",
		on_delete=models.CASCADE,
		related_name="notification_logs",
		null=True,
		blank=True,
	)
	notification_type = models.CharField(max_length=80, choices=NOTIFICATION_TYPE_CHOICES)
	channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default=CHANNEL_EMAIL)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
	subject = models.CharField(max_length=255)
	body = models.TextField()
	provider_message_id = models.CharField(max_length=255, blank=True)
	metadata = models.JSONField(default=dict, blank=True)
	dedupe_key = models.CharField(max_length=140, unique=True, null=True, blank=True)
	sent_at = models.DateTimeField(null=True, blank=True)
	failed_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["notification_type", "status"]),
			models.Index(fields=["recipient", "created_at"]),
		]

	def __str__(self):
		return f"{self.notification_type} -> {self.recipient.email} ({self.status})"
