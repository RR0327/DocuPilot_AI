from django.db import migrations, models
import core.models


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]
    operations = [migrations.AddField(model_name="document", name="file", field=models.FileField(blank=True, max_length=512, upload_to=core.models.private_document_path))]
