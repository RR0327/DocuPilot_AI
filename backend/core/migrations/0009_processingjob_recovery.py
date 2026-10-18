from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("core", "0008_processingjob")]
    operations = [
        migrations.AddField(model_name="processingjob", name="recovery_count", field=models.PositiveIntegerField(default=0)),
        migrations.AddField(model_name="processingjob", name="last_recovery_at", field=models.DateTimeField(null=True, blank=True)),
    ]
