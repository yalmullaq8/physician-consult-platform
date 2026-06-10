from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from physicians.models import PhysicianProfile, Specialty


class Command(BaseCommand):
    help = "Seed initial specialties and sample physician profiles"

    @transaction.atomic
    def handle(self, *args, **options):
        specialties = [
            "Cardiology",
            "Dermatology",
            "Endocrinology",
            "Gastroenterology",
            "Neurology",
            "Obstetrics and Gynecology",
            "Oncology",
            "Orthopedics",
            "Pediatrics",
            "Psychiatry",
            "Radiology",
            "Urology",
        ]

        specialty_map = {}
        for index, name in enumerate(specialties, start=1):
            specialty, _ = Specialty.objects.get_or_create(
                name=name,
                defaults={"display_order": index, "is_active": True},
            )
            specialty_map[name] = specialty

        sample_physicians = [
            {
                "email": "dr.amina.alsalem@example.com",
                "full_name": "Dr. Amina Al Salem",
                "specialty": "Cardiology",
                "license_country": "Kuwait",
                "hospital_or_clinic": "Kuwait Heart Center",
                "years_of_experience": 12,
                "consultation_price": "150.00",
                "consultation_duration_minutes": 30,
                "bio": "Interventional cardiologist focused on complex cardiac cases.",
            },
            {
                "email": "dr.omar.alrashid@example.com",
                "full_name": "Dr. Omar Al Rashid",
                "specialty": "Neurology",
                "license_country": "Kuwait",
                "hospital_or_clinic": "Al Salam Specialist Hospital",
                "years_of_experience": 10,
                "consultation_price": "140.00",
                "consultation_duration_minutes": 30,
                "bio": "Neurologist with expertise in stroke and neurocritical care.",
            },
            {
                "email": "dr.sara.alhaddad@example.com",
                "full_name": "Dr. Sara Al Haddad",
                "specialty": "Dermatology",
                "license_country": "Kuwait",
                "hospital_or_clinic": "Royal Care Clinic",
                "years_of_experience": 8,
                "consultation_price": "120.00",
                "consultation_duration_minutes": 20,
                "bio": "Dermatologist specializing in complex inflammatory skin disorders.",
            },
        ]

        for physician in sample_physicians:
            user, created = User.objects.get_or_create(
                email=physician["email"],
                defaults={
                    "full_name": physician["full_name"],
                    "phone_number": "",
                    "is_active": True,
                },
            )
            if created:
                user.set_password("ChangeMe123!")
                user.save(update_fields=["password"])

            PhysicianProfile.objects.get_or_create(
                user=user,
                defaults={
                    "full_name": physician["full_name"],
                    "specialty": specialty_map[physician["specialty"]],
                    "professional_title": "Consultant",
                    "license_country": physician.get("license_country", ""),
                    "hospital_or_clinic": physician["hospital_or_clinic"],
                    "years_of_experience": physician["years_of_experience"],
                    "bio": physician["bio"],
                    "consultation_price": physician["consultation_price"],
                    "consultation_duration_minutes": physician["consultation_duration_minutes"],
                    "is_verified": True,
                    "accepts_bookings": True,
                },
            )

        self.stdout.write(self.style.SUCCESS("Initial specialties and sample physicians seeded successfully."))
