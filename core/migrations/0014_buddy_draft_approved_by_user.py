from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0013_buddy_draft_v1"),
    ]

    operations = [
        migrations.AddField(
            model_name="buddydraft",
            name="approved_by_user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="approved_buddy_drafts",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
