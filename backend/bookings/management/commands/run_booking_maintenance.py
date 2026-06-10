from django.core.management.base import BaseCommand

from bookings.tasks import (
    expire_unpaid_bookings_task,
    mark_past_bookings_ready_for_completion_task,
)


class Command(BaseCommand):
    help = "Run booking maintenance tasks: expire unpaid bookings and mark completed bookings."

    def add_arguments(self, parser):
        parser.add_argument(
            "--expiry-minutes",
            type=int,
            default=30,
            help="Pending payment expiry threshold in minutes.",
        )
        parser.add_argument(
            "--grace-minutes",
            type=int,
            default=15,
            help="Grace window after scheduled end before marking completed.",
        )

    def handle(self, *args, **options):
        expired = expire_unpaid_bookings_task(expiry_minutes=options["expiry_minutes"])
        completed = mark_past_bookings_ready_for_completion_task(
            grace_minutes=options["grace_minutes"]
        )

        self.stdout.write(self.style.SUCCESS(f"Expired unpaid bookings: {expired}"))
        self.stdout.write(self.style.SUCCESS(f"Marked completed bookings: {completed}"))
