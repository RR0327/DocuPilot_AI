from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("core", "0005_chunkembedding")]
    operations = [
        migrations.CreateModel(
            name="InvoiceLineItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("line_number", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("description", models.CharField(max_length=255)),
                ("quantity", models.DecimalField(max_digits=14, decimal_places=3)),
                ("unit_price", models.DecimalField(max_digits=16, decimal_places=2)),
                ("line_total", models.DecimalField(max_digits=16, decimal_places=2)),
                ("calculated_total", models.DecimalField(max_digits=16, decimal_places=2)),
                ("validation_status", models.CharField(max_length=12, choices=[("matched", "Matched"), ("mismatch", "Mismatch")])),
                ("page_number", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("source_excerpt", models.CharField(max_length=500)),
                ("record", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="line_items", to="core.extractedrecord")),
            ],
            options={"ordering": ["record_id", "line_number"]},
        ),
        migrations.AddConstraint(model_name="invoicelineitem", constraint=models.UniqueConstraint(fields=("record", "line_number"), name="unique_invoice_line_number")),
    ]
