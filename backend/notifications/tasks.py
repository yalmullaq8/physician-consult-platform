from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from bookings.models import Booking

from .services import (
    send_booking_confirmed_notifications,
    send_consultation_reminder,
    send_payment_failed_notification,
)


@shared_task(name="notifications.tasks.send_booking_confirmed_notifications_task")
def send_booking_confirmed_notifications_task(booking_id: int):
    booking = Booking.objects.filter(pk=booking_id).first()
    if booking is None:
        return False
    send_booking_confirmed_notifications(booking)
    return True


@shared_task(name="notifications.tasks.send_payment_failed_notification_task")
def send_payment_failed_notification_task(booking_id: int, payment_status: str):
    booking = Booking.objects.filter(pk=booking_id).first()
    if booking is None:
        return False
    send_payment_failed_notification(booking, payment_status)
    return True


def _reminder_window(hours_before: int, window_minutes: int = 15):
    now = timezone.now()
    target_start = now + timedelta(hours=hours_before)
    target_end = target_start + timedelta(minutes=window_minutes)
    return target_start, target_end


@shared_task(name="notifications.tasks.send_24h_consultation_reminders_task")
def send_24h_consultation_reminders():
    start, end = _reminder_window(hours_before=24)
    bookings = Booking.objects.filter(
        status=Booking.STATUS_CONFIRMED,
        scheduled_start__gte=start,
        scheduled_start__lt=end,
    )
    for booking in bookings:
        send_consultation_reminder(booking, hours_before=24)
    return bookings.count()


@shared_task(name="notifications.tasks.send_1h_consultation_reminders_task")
def send_1h_consultation_reminders():
    start, end = _reminder_window(hours_before=1)
    bookings = Booking.objects.filter(
        status=Booking.STATUS_CONFIRMED,
        scheduled_start__gte=start,
        scheduled_start__lt=end,
    )
    for booking in bookings:
        send_consultation_reminder(booking, hours_before=1)
    return bookings.count()
