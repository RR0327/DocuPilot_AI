from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("core", "0004_invoicepaymentstate")]
    operations = [
        migrations.CreateModel(
            name="ChunkEmbedding",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("model_name", models.CharField(max_length=200)),
                ("vector", models.JSONField()),
                ("chunk", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="embeddings", to="core.documentchunk")),
            ],
        ),
        migrations.AddConstraint(model_name="chunkembedding", constraint=models.UniqueConstraint(fields=("chunk", "model_name"), name="unique_chunk_embedding_model")),
    ]
