from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("core", "0009_processingjob_recovery")]

    operations = [
        migrations.CreateModel(
            name="DocumentClassification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("category", models.CharField(choices=[("invoice", "Invoice"), ("policy", "Policy"), ("report", "Report"), ("contract", "Contract"), ("unknown", "Unknown")], default="unknown", max_length=12)),
                ("evidence", models.JSONField(default=list)),
                ("scores", models.JSONField(default=dict)),
                ("reason", models.CharField(blank=True, max_length=180)),
                ("classified_at", models.DateTimeField(auto_now=True)),
                ("document", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="classification", to="core.document")),
            ],
        ),
    ]
