from django.db import migrations


def copy_specialty_to_specialties(apps, schema_editor):
    PhysicianProfile = apps.get_model("physicians", "PhysicianProfile")

    for physician in PhysicianProfile.objects.exclude(specialty_id__isnull=True):
        physician.specialties.add(physician.specialty_id)


class Migration(migrations.Migration):

    dependencies = [
        ("physicians", "0005_physicianprofile_specialties"),
    ]

    operations = [
        migrations.RunPython(copy_specialty_to_specialties, migrations.RunPython.noop),
    ]