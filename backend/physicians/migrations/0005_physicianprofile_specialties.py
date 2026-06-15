from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("physicians", "0004_alter_physicianavailability_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="physicianprofile",
            name="specialties",
            field=models.ManyToManyField(related_name="physician_profiles", to="physicians.specialty"),
        ),
    ]