from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [("core", "0002_document_file")]
    operations = [
        migrations.CreateModel(
            name="DocumentChunk",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("page_number", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("chunk_index", models.PositiveIntegerField()),
                ("start_offset", models.PositiveIntegerField()),
                ("end_offset", models.PositiveIntegerField()),
                ("content", models.TextField()),
                ("document", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chunks", to="core.document")),
            ],
            options={"ordering": ["document_id", "page_number", "chunk_index"]},
        ),
        migrations.AddConstraint(model_name="documentchunk", constraint=models.UniqueConstraint(fields=("document", "page_number", "chunk_index"), name="unique_document_chunk")),
        migrations.AddIndex(model_name="documentchunk", index=models.Index(fields=["document", "page_number"], name="chunk_doc_page_idx")),
    ]
