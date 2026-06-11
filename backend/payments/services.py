from django.conf import settings
from django.db import transaction
from django.utils import timezone

from bookings.models import Booking

from .models import Payment
from .myfatoorah import (
    MyFatoorahAPIError,
    MyFatoorahConfigurationError,
    create_payment_url,
    get_available_payment_methods,
    get_payment_status,
)


class PaymentServiceError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def _parse_payment_status(status_text: str):
    normalized = (status_text or "").strip().lower()
    if normalized in {"paid", "success", "successful"}:
        return Payment.STATUS_PAID
    if normalized in {"failed", "error"}:
        return Payment.STATUS_FAILED
    if normalized in {"cancelled", "canceled"}:
        return Payment.STATUS_CANCELLED
    return Payment.STATUS_PENDING


@transaction.atomic
def initiate_myfatoorah_payment(booking: Booking, payment_method_id: int | None = None):
    payment, _ = Payment.objects.select_for_update().get_or_create(
        booking=booking,
        defaults={
            "provider": Payment.PROVIDER_MYFATOORAH,
            "amount": booking.consulting_physician.physician_profile.consultation_price,
            "currency": settings.DEFAULT_CURRENCY,
            "status": Payment.STATUS_INITIATED,
        },
    )

    if payment.status == Payment.STATUS_PAID:
        raise PaymentServiceError("payment_already_confirmed", "Payment for this booking is already confirmed.")

    # Attach the selected method for create_payment_url without schema changes.
    payment.selected_payment_method_id = payment_method_id

    try:
        created = create_payment_url(booking, payment)
    except MyFatoorahConfigurationError as exc:
        raise PaymentServiceError("payment_provider_not_configured", str(exc)) from exc
    except MyFatoorahAPIError as exc:
        error_text = str(exc)
        payment.status = Payment.STATUS_FAILED
        payment.failed_at = timezone.now()
        payment.raw_response = {"error": error_text}
        payment.save(update_fields=["status", "failed_at", "raw_response", "updated_at"])
        if "RedirectionURL is not valid" in error_text:
            raise PaymentServiceError(
                "payment_provider_not_configured",
                "Hosted payment page requires a public MYFATOORAH_HOSTED_REDIRECTION_URL (localhost is not accepted).",
            ) from exc
        raise PaymentServiceError("payment_failed", "Unable to initialize payment at this time.") from exc

    payment.provider_invoice_id = created["provider_invoice_id"]
    payment.provider_payment_id = created["provider_payment_id"]
    payment.raw_request = created["raw_request"]
    payment.raw_response = created["raw_response"]
    payment.status = Payment.STATUS_PENDING
    payment.save(
        update_fields=[
            "provider_invoice_id",
            "provider_payment_id",
            "raw_request",
            "raw_response",
            "status",
            "updated_at",
        ]
    )

    return payment, created["payment_url"]


def list_myfatoorah_payment_methods(invoice_amount: float):
    try:
        return get_available_payment_methods(invoice_amount)
    except MyFatoorahConfigurationError as exc:
        raise PaymentServiceError("payment_provider_not_configured", str(exc)) from exc
    except MyFatoorahAPIError as exc:
        raise PaymentServiceError("payment_failed", str(exc)) from exc


@transaction.atomic
def confirm_myfatoorah_payment(payment_identifier):
    key_type = "InvoiceId"
    status_response = None
    payment = Payment.objects.select_for_update().filter(
        provider=Payment.PROVIDER_MYFATOORAH,
        provider_invoice_id=str(payment_identifier),
    ).first()

    if not payment:
        payment = Payment.objects.select_for_update().filter(
            provider=Payment.PROVIDER_MYFATOORAH,
            provider_payment_id=str(payment_identifier),
        ).first()
        key_type = "PaymentId"

    if not payment:
        # Callback identifiers vary by integration mode; resolve through provider status first.
        status_errors = []
        for candidate_key_type in ("InvoiceId", "PaymentId"):
            try:
                status_response = get_payment_status(payment_identifier, key_type=candidate_key_type)
                break
            except MyFatoorahConfigurationError as exc:
                raise PaymentServiceError("payment_provider_not_configured", str(exc)) from exc
            except MyFatoorahAPIError as exc:
                status_errors.append(str(exc))

        if not status_response:
            raise PaymentServiceError(
                "payment_failed",
                status_errors[-1] if status_errors else "Unable to verify payment status.",
            )

        data = status_response.get("Data") or {}
        resolved_invoice_id = str(data.get("InvoiceId") or "").strip()
        resolved_payment_id = str(data.get("PaymentId") or "").strip()

        if resolved_invoice_id:
            payment = Payment.objects.select_for_update().filter(
                provider=Payment.PROVIDER_MYFATOORAH,
                provider_invoice_id=resolved_invoice_id,
            ).first()

        if not payment and resolved_payment_id:
            payment = Payment.objects.select_for_update().filter(
                provider=Payment.PROVIDER_MYFATOORAH,
                provider_payment_id=resolved_payment_id,
            ).first()

        if not payment:
            raise PaymentServiceError("booking_not_found", "Payment record not found.")

    if status_response is None:
        try:
            status_response = get_payment_status(payment_identifier, key_type=key_type)
        except MyFatoorahConfigurationError as exc:
            raise PaymentServiceError("payment_provider_not_configured", str(exc)) from exc
        except MyFatoorahAPIError as exc:
            raise PaymentServiceError("payment_failed", str(exc)) from exc

    data = status_response.get("Data") or {}
    invoice_status = data.get("InvoiceStatus") or data.get("PaymentStatus")
    resolved_status = _parse_payment_status(invoice_status)

    payment.provider_invoice_id = str(data.get("InvoiceId") or payment.provider_invoice_id or "")
    payment.provider_payment_id = str(data.get("PaymentId") or payment.provider_payment_id or "")
    payment.raw_response = status_response
    previous_status = payment.status

    if resolved_status == Payment.STATUS_PAID:
        payment.status = Payment.STATUS_PAID
        payment.paid_at = timezone.now()
        payment.failed_at = None
        payment.booking.status = Booking.STATUS_CONFIRMED
        payment.booking.save(update_fields=["status", "updated_at"])
        if previous_status != Payment.STATUS_PAID:
            from audit.services import log_audit_event
            from notifications.services import send_booking_confirmed_notifications

            log_audit_event(
                action="payment_mark_paid",
                obj=payment,
                metadata={
                    "booking_reference": payment.booking.booking_reference,
                    "previous_status": previous_status,
                    "new_status": payment.status,
                },
            )
            send_booking_confirmed_notifications(payment.booking)
    elif resolved_status == Payment.STATUS_FAILED:
        payment.status = Payment.STATUS_FAILED
        payment.failed_at = timezone.now()
        if previous_status != Payment.STATUS_FAILED:
            from audit.services import log_audit_event
            from notifications.services import send_payment_failed_notification

            log_audit_event(
                action="payment_mark_failed",
                obj=payment,
                metadata={
                    "booking_reference": payment.booking.booking_reference,
                    "previous_status": previous_status,
                    "new_status": payment.status,
                },
            )
            send_payment_failed_notification(payment.booking, payment.status)
    elif resolved_status == Payment.STATUS_CANCELLED:
        payment.status = Payment.STATUS_CANCELLED
        payment.failed_at = timezone.now()
        if previous_status != Payment.STATUS_CANCELLED:
            from audit.services import log_audit_event
            from notifications.services import send_payment_failed_notification

            log_audit_event(
                action="payment_mark_cancelled",
                obj=payment,
                metadata={
                    "booking_reference": payment.booking.booking_reference,
                    "previous_status": previous_status,
                    "new_status": payment.status,
                },
            )
            send_payment_failed_notification(payment.booking, payment.status)
    else:
        payment.status = Payment.STATUS_PENDING

    payment.save(
        update_fields=[
            "provider_invoice_id",
            "provider_payment_id",
            "raw_response",
            "status",
            "paid_at",
            "failed_at",
            "updated_at",
        ]
    )

    return payment


def handle_myfatoorah_webhook(payload: dict):
    payment_id = payload.get("PaymentId") or payload.get("InvoiceId") or payload.get("Data", {}).get("PaymentId")
    if not payment_id:
        raise PaymentServiceError("payment_failed", "Webhook payload does not include payment identifier.")

    return confirm_myfatoorah_payment(payment_id)
