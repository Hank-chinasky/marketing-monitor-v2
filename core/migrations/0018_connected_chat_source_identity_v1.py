from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0017_conversation_message"),
    ]

    operations = [
        migrations.AlterField(
            model_name="conversationthread",
            name="source_system",
            field=models.CharField(
                choices=[
                    ("mara_chat", "Mara chat"),
                    ("chatties", "Chatties"),
                ],
                default="mara_chat",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="conversationthread",
            name="source_site_id",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="conversationthread",
            name="source_site_label",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="conversationthread",
            name="source_participant_a_id",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="conversationthread",
            name="source_participant_b_id",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="conversationmessage",
            name="source_system",
            field=models.CharField(
                blank=True,
                choices=[
                    ("mara_chat", "Mara chat"),
                    ("chatties", "Chatties"),
                ],
                default="",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="conversationmessage",
            name="source_site_id",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="conversationmessage",
            name="source_thread_id",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="conversationmessage",
            name="source_sender_id",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="conversationmessage",
            name="source_recipient_id",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
    ]
