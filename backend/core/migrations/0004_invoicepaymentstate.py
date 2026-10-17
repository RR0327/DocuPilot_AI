from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("core", "0003_documentchunk")]
    operations = [
        migrations.CreateModel(
            name="InvoicePaymentState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("unknown", "Unknown"), ("pending", "Pending"), ("paid", "Paid"), ("disputed", "Disputed")], default="unknown", max_length=12)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("record", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="payment_state", to="core.extractedrecord")),
            ],
        ),
    ]
