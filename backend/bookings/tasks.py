from celery import shared_task

from .services import expire_unpaid_bookings, mark_past_bookings_ready_for_completion


@shared_task(name="bookings.tasks.expire_unpaid_bookings_task")
def expire_unpaid_bookings_task(expiry_minutes: int = 30):
    return expire_unpaid_bookings(expiry_minutes=expiry_minutes)


@shared_task(name="bookings.tasks.mark_past_bookings_ready_for_completion_task")
def mark_past_bookings_ready_for_completion_task(grace_minutes: int = 15):
    return mark_past_bookings_ready_for_completion(grace_minutes=grace_minutes)
