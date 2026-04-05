from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_conversation_thread_v1"),
    ]

    operations = [
        migrations.CreateModel(
            name="BuddyDraft",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reply_text", models.TextField()),
                ("intent", models.CharField(max_length=100)),
                ("tone", models.CharField(max_length=100)),
                ("confidence", models.DecimalField(blank=True, decimal_places=3, max_digits=4, null=True)),
                (
                    "risk_level",
                    models.CharField(
                        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")],
                        max_length=20,
                    ),
                ),
                ("requires_human_attention", models.BooleanField(default=True)),
                ("handoff_note", models.TextField(blank=True)),
                (
                    "state",
                    models.CharField(
                        choices=[("drafted", "Drafted"), ("approved", "Approved"), ("rejected", "Rejected")],
                        default="drafted",
                        max_length=20,
                    ),
                ),
                (
                    "generation_source",
                    models.CharField(
                        choices=[("stub", "Stub"), ("buddy_api", "Buddy API")],
                        default="stub",
                        max_length=20,
                    ),
                ),
                ("edited_after_generation", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("rejected_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_for_operator",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="buddy_drafts_created_for",
                        to="core.operator",
                    ),
                ),
                (
                    "thread",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="buddy_drafts",
                        to="core.conversationthread",
                    ),
                ),
            ],
        ),
    ]