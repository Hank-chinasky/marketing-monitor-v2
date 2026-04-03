from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_creator_primary_link"),
    ]

    operations = [
        migrations.AddField(
            model_name="creatorchannel",
            name="session_blockers",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="creatorchannel",
            name="session_next_action",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="creatorchannel",
            name="session_policy_context_reviewed",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="creatorchannel",
            name="session_updated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="creatorchannel",
            name="session_what_done",
            field=models.TextField(blank=True, default=""),
        ),
    ]