from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0010_documentclassification"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="ClassificationFeedback",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("verify", "Verify prediction"), ("override", "Override prediction"), ("clear", "Clear human decision")], max_length=10)),
                ("category", models.CharField(blank=True, choices=[("invoice", "Invoice"), ("policy", "Policy"), ("report", "Report"), ("contract", "Contract"), ("unknown", "Unknown")], max_length=12)),
                ("machine_category", models.CharField(choices=[("invoice", "Invoice"), ("policy", "Policy"), ("report", "Report"), ("contract", "Contract"), ("unknown", "Unknown")], max_length=12)),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("document", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="classification_feedback", to="core.document")),
                ("reviewer", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="classification_feedback", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.AddIndex(model_name="classificationfeedback", index=models.Index(fields=["document", "created_at"], name="class_feedback_doc_time")),
    ]
