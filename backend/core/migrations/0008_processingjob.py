from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [("core", "0007_extractionreview")]
    operations = [
        migrations.CreateModel(
            name="ProcessingJob",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("state", models.CharField(choices=[("queued", "Queued"), ("running", "Running"), ("succeeded", "Succeeded"), ("failed", "Failed")], default="queued", max_length=12)),
                ("attempt", models.PositiveIntegerField(default=1)),
                ("error_message", models.CharField(blank=True, max_length=300)),
                ("page_count", models.PositiveIntegerField(default=0)),
                ("character_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("document", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="processing_jobs", to="core.document")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(model_name="processingjob", index=models.Index(fields=["document", "state"], name="processing_doc_state_idx")),
    ]
