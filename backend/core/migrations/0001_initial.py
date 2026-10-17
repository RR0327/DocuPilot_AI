# Generated for DocuPilot AI Phase 0 Step 2 — Django 5.2 migration format.
import django.db.models.deletion
import django.core.validators
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Document",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("file_type", models.CharField(default="pdf", max_length=20)),
                ("original_filename", models.CharField(blank=True, max_length=255)),
                ("processing_status", models.CharField(choices=[("pending", "Pending"), ("processing", "Processing"), ("completed", "Completed"), ("failed", "Failed")], default="pending", max_length=20)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="documents", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-uploaded_at", "-id"]},
        ),
        migrations.CreateModel(
            name="DocumentPage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("page_number", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("extracted_text", models.TextField(blank=True)),
                ("document", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="pages", to="core.document")),
            ],
            options={"ordering": ["page_number"]},
        ),
        migrations.CreateModel(
            name="ExtractedRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("record_type", models.CharField(max_length=50)),
                ("extracted_data", models.JSONField(default=dict)),
                ("validation_status", models.CharField(choices=[("unreviewed", "Unreviewed"), ("valid", "Valid"), ("invalid", "Invalid")], default="unreviewed", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("document", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="extracted_records", to="core.document")),
            ],
        ),
        migrations.CreateModel(
            name="QuestionAnswer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("question", models.TextField()),
                ("answer", models.TextField()),
                ("source_references", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="questions", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(model_name="documentpage", constraint=models.UniqueConstraint(fields=("document", "page_number"), name="unique_document_page")),
    ]
