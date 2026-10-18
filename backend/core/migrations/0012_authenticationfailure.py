from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):
    dependencies = [("core", "0011_classificationfeedback")]
    operations = [migrations.CreateModel(name="AuthenticationFailure", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("key_digest", models.CharField(db_index=True, max_length=64, unique=True)),
        ("attempts", models.PositiveIntegerField(default=0)),
        ("window_started", models.DateTimeField()),
        ("last_attempt", models.DateTimeField(auto_now=True)),
    ], options={"verbose_name": "Authentication failure bucket"})]
