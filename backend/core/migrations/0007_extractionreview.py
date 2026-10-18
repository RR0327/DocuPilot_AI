from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_invoicelineitem"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="ExtractionReview",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("approve", "Approve"), ("reject", "Reject"), ("reopen", "Reopen")], max_length=12)),
                ("previous_status", models.CharField(max_length=20)),
                ("new_status", models.CharField(max_length=20)),
                ("corrections", models.JSONField(default=dict)),
                ("note", models.TextField(blank=True)),
                ("reviewed_at", models.DateTimeField(auto_now_add=True)),
                ("record", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reviews", to="core.extractedrecord")),
                ("reviewer", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="extraction_reviews", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-reviewed_at", "-id"]},
        )
    ]
