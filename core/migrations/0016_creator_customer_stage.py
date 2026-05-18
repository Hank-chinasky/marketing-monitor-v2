from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0015_approval_v1"),
    ]

    operations = [
        migrations.AddField(
            model_name="creator",
            name="customer_stage",
            field=models.CharField(
                choices=[
                    ("unknown", "Unknown"),
                    ("lead", "Lead"),
                    ("outside_paywall", "Outside paywall"),
                    ("inside_paywall", "Inside paywall"),
                    ("former_customer", "Former customer"),
                    ("blocked_do_not_contact", "Blocked / do not contact"),
                ],
                default="unknown",
                max_length=30,
            ),
        ),
    ]
