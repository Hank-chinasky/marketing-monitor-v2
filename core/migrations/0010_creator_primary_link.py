from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_creatormaterial"),
    ]

    operations = [
        migrations.AddField(
            model_name="creator",
            name="primary_link",
            field=models.URLField(blank=True),
        ),
    ]
