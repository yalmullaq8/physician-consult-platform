from datetime import timedelta
import json
from urllib import error, request

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import NotificationLog


def _send_email(log: NotificationLog):
    provider = getattr(settings, "EMAIL_PROVIDER", "smtp").strip().lower()

    if provider == "resend":
        return _send_email_via_resend(log)

    return _send_email_via_smtp(log)


def _send_email_via_smtp(log: NotificationLog):
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@physician-consult.local")
    send_mail(
        subject=log.subject,
        message=log.body,
        from_email=from_email,
        recipient_list=[log.recipient.email],
        fail_silently=False,
    )
    return "smtp"


def _send_email_via_resend(log: NotificationLog):
    api_key = getattr(settings, "RESEND_API_KEY", "")
    if not api_key:
        raise RuntimeError("RESEND_API_KEY is not configured.")

    api_url = getattr(settings, "RESEND_API_URL", "https://api.resend.com/emails")
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@physician-consult.local")
    payload = {
        "from": from_email,
        "to": [log.recipient.email],
        "subject": log.subject,
        "text": log.body,
    }

    req = request.Request(
        url=api_url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            # Cloudflare in front of api.resend.com blocks the default
            # "Python-urllib/x.y" agent (Error 1010), so send a normal one.
            "User-Agent": "physician-consult-platform/1.0",
        },
    )

    try:
        with request.urlopen(req, timeout=20) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body) if body else {}
            return str(data.get("id") or "resend")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8") if exc.fp else ""
        raise RuntimeError(body or str(exc)) from exc
    except error.URLError as exc:
        raise RuntimeError(str(exc)) from exc


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
    log = None
    if dedupe_key:
        existing = NotificationLog.objects.filter(dedupe_key=dedupe_key).first()
        if existing:
            # Already delivered successfully - nothing more to do.
            if existing.status == NotificationLog.STATUS_SENT:
                return existing
            # A prior attempt failed (or is still pending). Retry sending on the
            # same log row instead of short-circuiting forever.
            log = existing
            log.subject = subject
            log.body = body
            if metadata:
                log.metadata = {**(log.metadata or {}), **metadata}

    if log is None:
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
        provider_message_id = _send_email(log)
        log.status = NotificationLog.STATUS_SENT
        log.sent_at = timezone.now()
        log.failed_at = None
        log.provider_message_id = provider_message_id
        log.metadata = {k: v for k, v in (log.metadata or {}).items() if k != "error"}
    except Exception as exc:
        log.status = NotificationLog.STATUS_FAILED
        log.failed_at = timezone.now()
        log.metadata = {**(log.metadata or {}), "error": str(exc)}

    log.save(
        update_fields=[
            "status",
            "subject",
            "body",
            "sent_at",
            "failed_at",
            "provider_message_id",
            "metadata",
            "updated_at",
        ]
    )
    return log


def _build_video_conference_link(booking):
    base_url = getattr(
        settings,
        "VIDEO_CONFERENCE_PLACEHOLDER_BASE_URL",
        "https://meet.example.com/consult",
    )
    return f"{base_url.rstrip('/')}/{booking.booking_reference}"


def send_booking_confirmed_notifications(booking):
    start_local = timezone.localtime(booking.scheduled_start)
    formatted_start = start_local.strftime("%Y-%m-%d %I:%M %p %Z")
    video_link = _build_video_conference_link(booking)
    requester_details_block = (
        f"Requester details:\n"
        f"- Name: {booking.requester_name}\n"
        f"- Specialization: {booking.requester_specialization}\n"
        f"- Country of practice: {booking.requester_country_of_practice}\n"
        f"- Email: {booking.requester_email}\n"
        f"- WhatsApp: {booking.requester_whatsapp_number or 'Not provided'}"
    )

    requester_subject = f"Booking Confirmed: {booking.booking_reference}"
    requester_body = (
        f"Your consultation booking {booking.booking_reference} is confirmed.\n"
        f"Consulting physician: {booking.consulting_physician.full_name}\n"
        f"Scheduled start: {formatted_start}\n"
        f"Video conference link: {video_link}\n\n"
        f"{requester_details_block}"
    )
    create_and_send_notification(
        recipient=booking.requesting_physician,
        booking=booking,
        notification_type=NotificationLog.TYPE_BOOKING_CONFIRMED_REQUESTER,
        subject=requester_subject,
        body=requester_body,
        dedupe_key=f"booking_confirmed_requester:{booking.id}",
        metadata={"video_link": video_link},
    )

    consultant_subject = f"New Confirmed Consultation: {booking.booking_reference}"
    consultant_body = (
        f"A consultation booking {booking.booking_reference} has been confirmed.\n"
        f"Requesting account: {booking.requesting_physician.full_name}\n"
        f"Scheduled start: {formatted_start}\n"
        f"Video conference link: {video_link}\n\n"
        f"{requester_details_block}"
    )
    create_and_send_notification(
        recipient=booking.consulting_physician,
        booking=booking,
        notification_type=NotificationLog.TYPE_BOOKING_CONFIRMED_CONSULTANT,
        subject=consultant_subject,
        body=consultant_body,
        dedupe_key=f"booking_confirmed_consultant:{booking.id}",
        metadata={"video_link": video_link},
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
    formatted_start = start_local.strftime("%Y-%m-%d %I:%M %p %Z")
    video_link = _build_video_conference_link(booking)
    notification_type = (
        NotificationLog.TYPE_BOOKING_REMINDER_24H
        if hours_before == 24
        else NotificationLog.TYPE_BOOKING_REMINDER_1H
    )

    subject = f"Consultation Reminder ({hours_before}h): {booking.booking_reference}"
    body = (
        f"Reminder: Consultation {booking.booking_reference} starts at {formatted_start}.\n"
        f"Consulting physician: {booking.consulting_physician.full_name}\n"
        f"Requesting physician: {booking.requesting_physician.full_name}\n"
        f"Video conference link: {video_link}"
    )

    create_and_send_notification(
        recipient=booking.requesting_physician,
        booking=booking,
        notification_type=notification_type,
        subject=subject,
        body=body,
        dedupe_key=f"{notification_type}:{booking.id}:requester",
        metadata={"video_link": video_link},
    )
    create_and_send_notification(
        recipient=booking.consulting_physician,
        booking=booking,
        notification_type=notification_type,
        subject=subject,
        body=body,
        dedupe_key=f"{notification_type}:{booking.id}:consultant",
        metadata={"video_link": video_link},
    )
