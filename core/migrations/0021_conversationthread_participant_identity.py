from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0020_alter_conversationmessage_source_system_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="conversationthread",
            name="source_profile_label",
            field=models.CharField(blank=True, default="", max_length=160),
        ),
        migrations.AddField(
            model_name="conversationthread",
            name="source_profile_username",
            field=models.CharField(blank=True, default="", max_length=160),
        ),
        migrations.AddField(
            model_name="conversationthread",
            name="source_customer_label",
            field=models.CharField(blank=True, default="", max_length=160),
        ),
        migrations.AddField(
            model_name="conversationthread",
            name="source_customer_username",
            field=models.CharField(blank=True, default="", max_length=160),
        ),
    ]
