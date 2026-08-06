from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("organization", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="membership",
            name="role",
            field=models.CharField(
                choices=[
                    ("member", "Employee"),
                    ("supervisor", "Supervisor"),
                    ("chief", "Department chief"),
                ],
                default="member",
                max_length=20,
            ),
        )
    ]
