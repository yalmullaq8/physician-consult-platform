from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from physicians.models import PhysicianProfile
from physicians.services import validate_booking_slot

from .models import Booking


class BookingValidationError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def _generate_booking_reference():
    local_date = timezone.localdate()
    prefix = f"BK-{local_date.strftime('%Y%m%d')}"
    daily_count = Booking.objects.filter(booking_reference__startswith=prefix).count() + 1
    return f"{prefix}-{daily_count:04d}"


@transaction.atomic
def create_pending_booking(
    requesting_user,
    consulting_physician_profile: PhysicianProfile,
    scheduled_start,
    case_summary,
    requester_name,
    requester_specialization,
    requester_country_of_practice,
    requester_email,
    requester_whatsapp_number="",
):
    if not case_summary or not case_summary.strip():
        raise BookingValidationError("slot_unavailable", "Case summary is required.")

    if requesting_user.id == consulting_physician_profile.user_id:
        raise BookingValidationError("permission_denied", "You cannot book a consultation with yourself.")

    is_valid, scheduled_end, error_code, error_message = validate_booking_slot(
        consulting_physician_profile,
        scheduled_start,
    )

    if not is_valid:
        raise BookingValidationError(error_code, error_message)

    booking_reference = _generate_booking_reference()

    booking = Booking.objects.create(
        booking_reference=booking_reference,
        requesting_physician=requesting_user,
        consulting_physician=consulting_physician_profile.user,
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
        status=Booking.STATUS_PENDING_PAYMENT,
        case_summary=case_summary.strip(),
        requester_name=str(requester_name).strip(),
        requester_specialization=str(requester_specialization).strip(),
        requester_country_of_practice=str(requester_country_of_practice).strip(),
        requester_email=str(requester_email).strip().lower(),
        requester_whatsapp_number=str(requester_whatsapp_number).strip(),
    )

    return booking


@transaction.atomic
def expire_unpaid_bookings(expiry_minutes: int = 30):
    from audit.services import log_audit_event

    cutoff = timezone.now() - timedelta(minutes=expiry_minutes)
    bookings = Booking.objects.select_for_update().filter(
        status=Booking.STATUS_PENDING_PAYMENT,
        created_at__lte=cutoff,
    )

    expired_count = 0
    for booking in bookings:
        payment = getattr(booking, "payment", None)
        if payment and payment.status == "paid":
            booking.status = Booking.STATUS_CONFIRMED
            booking.save(update_fields=["status", "updated_at"])
            log_audit_event(
                action="booking_auto_confirm_paid_pending",
                obj=booking,
                metadata={"reason": "payment_already_paid", "expiry_minutes": expiry_minutes},
            )
            continue

        booking.status = Booking.STATUS_CANCELLED
        booking.cancellation_reason = "Booking expired due to unpaid invoice."
        booking.cancelled_at = timezone.now()
        booking.save(update_fields=["status", "cancellation_reason", "cancelled_at", "updated_at"])
        log_audit_event(
            action="booking_expired_unpaid",
            obj=booking,
            metadata={"expiry_minutes": expiry_minutes},
        )
        expired_count += 1

    return expired_count


@transaction.atomic
def mark_past_bookings_ready_for_completion(grace_minutes: int = 15):
    from audit.services import log_audit_event

    cutoff = timezone.now() - timedelta(minutes=grace_minutes)
    bookings = Booking.objects.select_for_update().filter(
        status=Booking.STATUS_CONFIRMED,
        scheduled_end__lte=cutoff,
    )

    booking_ids = list(bookings.values_list("id", flat=True))
    updated_count = bookings.update(status=Booking.STATUS_COMPLETED, updated_at=timezone.now())
    if updated_count:
        log_audit_event(
            action="booking_auto_mark_completed",
            object_type="bookings.Booking",
            object_id="bulk",
            metadata={"ids": booking_ids, "count": updated_count, "grace_minutes": grace_minutes},
        )
    return updated_count