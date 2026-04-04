from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_creatorchannel_workspace_session_discipline"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConversationThread",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "source_system",
                    models.CharField(
                        choices=[("mara_chat", "Mara chat")],
                        default="mara_chat",
                        max_length=32,
                    ),
                ),
                ("source_thread_id", models.CharField(max_length=255)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("waiting_on_operator", "Waiting on operator"),
                            ("waiting_on_customer", "Waiting on customer"),
                            ("handoff_required", "Handoff required"),
                            ("closed", "Closed"),
                        ],
                        default="active",
                        max_length=32,
                    ),
                ),
                ("last_message_at", models.DateTimeField(blank=True, null=True)),
                ("last_operator_handoff_at", models.DateTimeField(blank=True, null=True)),
                ("thread_summary", models.TextField(blank=True)),
                ("open_loop", models.TextField(blank=True)),
                ("guardrails", models.TextField(blank=True)),
                ("risk_flags", models.TextField(blank=True)),
                ("last_handoff_note", models.TextField(blank=True)),
                ("last_approved_reply_style", models.TextField(blank=True)),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "channel",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="conversation_threads",
                        to="core.creatorchannel",
                    ),
                ),
                (
                    "creator",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        related_name="conversation_threads",
                        to="core.creator",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="conversationthread",
            constraint=models.UniqueConstraint(
                fields=("source_system", "source_thread_id"),
                name="uniq_convthread_source_thread",
            ),
        ),
        migrations.AddIndex(
            model_name="conversationthread",
            index=models.Index(fields=["status"], name="convthread_status_idx"),
        ),
        migrations.AddIndex(
            model_name="conversationthread",
            index=models.Index(fields=["last_message_at"], name="convthread_last_msg_idx"),
        ),
    ]