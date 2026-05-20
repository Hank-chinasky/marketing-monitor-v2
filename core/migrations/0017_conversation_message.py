from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0016_creator_customer_stage"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConversationMessage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "direction",
                    models.CharField(
                        choices=[
                            ("inbound", "Inbound"),
                            ("outbound", "Outbound"),
                            ("internal_note", "Internal note"),
                        ],
                        max_length=20,
                    ),
                ),
                ("sender_label", models.CharField(blank=True, max_length=160)),
                ("source_message_id", models.CharField(blank=True, max_length=255)),
                ("body", models.TextField()),
                ("occurred_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "thread",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="conversation_messages",
                        to="core.conversationthread",
                    ),
                ),
            ],
            options={
                "ordering": ["occurred_at", "id"],
                "indexes": [
                    models.Index(
                        fields=["thread", "occurred_at"],
                        name="convmsg_thread_occurred_idx",
                    ),
                ],
            },
        ),
    ]
