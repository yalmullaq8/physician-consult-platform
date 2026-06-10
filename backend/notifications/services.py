from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import NotificationLog


def _send_email(log: NotificationLog):
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@physician-consult.local")
    send_mail(
        subject=log.subject,
        message=log.body,
        from_email=from_email,
        recipient_list=[log.recipient.email],
        fail_silently=False,
    )


def create_and_send_notification(
    *,
    recipient,
    notification_type: str,
    subject: str,
    body: str,
    booking=None,
    dedupe_key: str | None = None,
    metadata: dict | None = None,
):
    if dedupe_key:
        existing = NotificationLog.objects.filter(dedupe_key=dedupe_key).first()
        if existing:
            return existing

    log = NotificationLog.objects.create(
        recipient=recipient,
        booking=booking,
        notification_type=notification_type,
        subject=subject,
        body=body,
        dedupe_key=dedupe_key,
        metadata=metadata or {},
    )

    try:
        _send_email(log)
        log.status = NotificationLog.STATUS_SENT
        log.sent_at = timezone.now()
        log.failed_at = None
    except Exception as exc:
        log.status = NotificationLog.STATUS_FAILED
        log.failed_at = timezone.now()
        log.metadata = {**log.metadata, "error": str(exc)}

    log.save(update_fields=["status", "sent_at", "failed_at", "metadata", "updated_at"])
    return log


def send_booking_confirmed_notifications(booking):
    start_local = timezone.localtime(booking.scheduled_start)

    requester_subject = f"Booking Confirmed: {booking.booking_reference}"
    requester_body = (
        f"Your consultation booking {booking.booking_reference} is confirmed.\n"
        f"Consulting physician: {booking.consulting_physician.full_name}\n"
        f"Scheduled start: {start_local.isoformat()}"
    )
    create_and_send_notification(
        recipient=booking.requesting_physician,
        booking=booking,
        notification_type=NotificationLog.TYPE_BOOKING_CONFIRMED_REQUESTER,
        subject=requester_subject,
        body=requester_body,
        dedupe_key=f"booking_confirmed_requester:{booking.id}",
    )

    consultant_subject = f"New Confirmed Consultation: {booking.booking_reference}"
    consultant_body = (
        f"A consultation booking {booking.booking_reference} has been confirmed.\n"
        f"Requesting physician: {booking.requesting_physician.full_name}\n"
        f"Scheduled start: {start_local.isoformat()}"
    )
    create_and_send_notification(
        recipient=booking.consulting_physician,
        booking=booking,
        notification_type=NotificationLog.TYPE_BOOKING_CONFIRMED_CONSULTANT,
        subject=consultant_subject,
        body=consultant_body,
        dedupe_key=f"booking_confirmed_consultant:{booking.id}",
    )


def send_payment_failed_notification(booking, payment_status: str):
    subject = f"Payment Issue for Booking {booking.booking_reference}"
    body = (
        f"We could not confirm your payment for booking {booking.booking_reference}.\n"
        f"Current payment status: {payment_status}.\n"
        "Please retry payment to confirm this consultation slot."
    )
    create_and_send_notification(
        recipient=booking.requesting_physician,
        booking=booking,
        notification_type=NotificationLog.TYPE_PAYMENT_FAILED,
        subject=subject,
        body=body,
        dedupe_key=f"payment_failed:{booking.id}:{payment_status}",
    )


def send_consultation_reminder(booking, hours_before: int):
    start_local = timezone.localtime(booking.scheduled_start)
    notification_type = (
        NotificationLog.TYPE_BOOKING_REMINDER_24H
        if hours_before == 24
        else NotificationLog.TYPE_BOOKING_REMINDER_1H
    )

    subject = f"Consultation Reminder ({hours_before}h): {booking.booking_reference}"
    body = (
        f"Reminder: Consultation {booking.booking_reference} starts at {start_local.isoformat()}.\n"
        f"Consulting physician: {booking.consulting_physician.full_name}\n"
        f"Requesting physician: {booking.requesting_physician.full_name}"
    )

    create_and_send_notification(
        recipient=booking.requesting_physician,
        booking=booking,
        notification_type=notification_type,
        subject=subject,
        body=body,
        dedupe_key=f"{notification_type}:{booking.id}:requester",
    )
    create_and_send_notification(
        recipient=booking.consulting_physician,
        booking=booking,
        notification_type=notification_type,
        subject=subject,
        body=body,
        dedupe_key=f"{notification_type}:{booking.id}:consultant",
    )
