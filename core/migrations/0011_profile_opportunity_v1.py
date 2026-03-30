from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0010_creator_primary_link"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProfileOpportunity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("intake_name", models.CharField(max_length=255)),
                ("profile_url", models.URLField(blank=True)),
                ("intake_notes", models.TextField(blank=True)),
                ("handoff_note", models.TextField(blank=True)),
                ("source_quality_score", models.PositiveSmallIntegerField(choices=[(0, "0"), (1, "1"), (2, "2")], default=0)),
                ("profile_signal_score", models.PositiveSmallIntegerField(choices=[(0, "0"), (1, "1"), (2, "2")], default=0)),
                ("intent_guess_score", models.PositiveSmallIntegerField(choices=[(0, "0"), (1, "1"), (2, "2")], default=0)),
                ("target_fit_score", models.PositiveSmallIntegerField(choices=[(0, "0"), (1, "1"), (2, "2")], default=0)),
                ("risk_penalty_score", models.SmallIntegerField(choices=[(-2, "-2"), (-1, "-1"), (0, "0")], default=0)),
                ("total_score", models.SmallIntegerField(default=0, editable=False)),
                ("priority_band", models.CharField(choices=[("high", "High"), ("medium", "Medium"), ("low", "Low")], default="low", editable=False, max_length=16)),
                ("action_bucket", models.CharField(choices=[("nu_oppakken", "Nu oppakken"), ("later", "Later"), ("niet_waard", "Niet waard")], default="niet_waard", editable=False, max_length=24)),
                ("score_reason_short", models.CharField(blank=True, editable=False, max_length=255)),
                ("manual_override", models.BooleanField(default=False)),
                ("override_priority_band", models.CharField(blank=True, choices=[("high", "High"), ("medium", "Medium"), ("low", "Low")], max_length=16)),
                ("override_action_bucket", models.CharField(blank=True, choices=[("nu_oppakken", "Nu oppakken"), ("later", "Later"), ("niet_waard", "Niet waard")], max_length=24)),
                ("override_reason_short", models.CharField(blank=True, max_length=140)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "assigned_to",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_profile_opportunities",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-updated_at", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="OutcomeEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("outcome_type", models.CharField(choices=[("geen_reactie", "Geen reactie"), ("gesprek_gestart", "Gesprek gestart"), ("warm_vervolg", "Warm vervolg"), ("conversion", "Conversion"), ("afgevallen", "Afgevallen"), ("onduidelijk", "Onduidelijk")], max_length=32)),
                ("notes", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="profile_opportunity_outcomes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "opportunity",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="outcomes",
                        to="core.profileopportunity",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "-id"],
            },
        ),
    ]
