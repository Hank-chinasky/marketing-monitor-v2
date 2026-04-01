from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0011_profile_opportunity_v1"),
    ]

    operations = [
        migrations.CreateModel(
            name="CreatorBoardWorkItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("status", models.CharField(choices=[("new", "Nieuw"), ("in_progress", "In uitvoering"), ("blocked", "Geblokkeerd"), ("done", "Afgerond")], default="new", max_length=24)),
                ("priority", models.CharField(choices=[("high", "High"), ("medium", "Medium"), ("low", "Low")], default="medium", max_length=16)),
                ("source_type", models.CharField(choices=[("manual_intake", "Handmatige intake"), ("creator", "Creator"), ("channel", "Channel"), ("other", "Overig")], default="manual_intake", max_length=24)),
                ("summary", models.TextField(blank=True)),
                ("next_action", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "assigned_to",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_creatorboard_work_items",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-updated_at", "-created_at"],
            },
        ),
    ]