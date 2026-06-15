from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("physicians", "0006_copy_physician_specialty_to_specialties"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="physicianprofile",
            name="specialty",
        ),
    ]