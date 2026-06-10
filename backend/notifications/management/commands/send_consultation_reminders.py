from django.core.management.base import BaseCommand

from notifications.tasks import (
    send_1h_consultation_reminders,
    send_24h_consultation_reminders,
)


class Command(BaseCommand):
    help = "Send pending 24h and 1h consultation reminders."

    def handle(self, *args, **options):
        reminders_24h = send_24h_consultation_reminders()
        reminders_1h = send_1h_consultation_reminders()

        self.stdout.write(self.style.SUCCESS(f"24h reminders sent: {reminders_24h}"))
        self.stdout.write(self.style.SUCCESS(f"1h reminders sent: {reminders_1h}"))
