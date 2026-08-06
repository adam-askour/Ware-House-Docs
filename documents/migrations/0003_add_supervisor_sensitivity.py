from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("documents", "0002_alter_storedfile_sha256")]

    operations = [
        migrations.AlterField(
            model_name="document",
            name="sensitivity",
            field=models.CharField(
                choices=[
                    ("normal", "Normal"),
                    ("supervisor", "Supervisor"),
                    ("confidential", "Chief only"),
                ],
                default="normal",
                max_length=20,
            ),
        )
    ]
