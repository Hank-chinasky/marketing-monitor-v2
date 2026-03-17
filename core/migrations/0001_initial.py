from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Operator",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="operator_profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Creator",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("display_name", models.CharField(max_length=160)),
                ("legal_name", models.CharField(blank=True, max_length=200)),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Active"), ("paused", "Paused"), ("offboarded", "Offboarded")],
                        max_length=20,
                    ),
                ),
                (
                    "consent_status",
                    models.CharField(
                        choices=[("pending", "Pending"), ("active", "Active"), ("revoked", "Revoked")],
                        max_length=20,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                (
                    "primary_operator",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="primary_creators",
                        to="core.operator",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CreatorChannel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "platform",
                    models.CharField(
                        choices=[
                            ("instagram", "Instagram"),
                            ("tiktok", "TikTok"),
                            ("telegram", "Telegram"),
                            ("other", "Other"),
                        ],
                        max_length=20,
                    ),
                ),
                ("handle", models.CharField(max_length=160)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("paused", "Paused"),
                            ("restricted", "Restricted"),
                            ("banned", "Banned"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "access_mode",
                    models.CharField(
                        choices=[
                            ("creator_only", "Creator only"),
                            ("operator_with_approval", "Operator with approval"),
                            ("operator_direct", "Operator direct"),
                            ("draft_only", "Draft only"),
                        ],
                        max_length=40,
                    ),
                ),
                (
                    "recovery_owner",
                    models.CharField(
                        choices=[("creator", "Creator"), ("agency", "Agency"), ("shared", "Shared")],
                        max_length=20,
                    ),
                ),
                (
                    "creator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="channels",
                        to="core.creator",
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("platform", "handle"),
                        name="uniq_platform_handle_exact",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="OperatorAssignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "scope",
                    models.CharField(
                        choices=[
                            ("full_management", "Full management"),
                            ("posting_only", "Posting only"),
                            ("draft_only", "Draft only"),
                            ("analytics_only", "Analytics only"),
                        ],
                        max_length=30,
                    ),
                ),
                ("starts_at", models.DateTimeField()),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                ("active", models.BooleanField(default=True)),
                (
                    "creator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assignments",
                        to="core.creator",
                    ),
                ),
                (
                    "operator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assignments",
                        to="core.operator",
                    ),
                ),
            ],
        ),
    ]
