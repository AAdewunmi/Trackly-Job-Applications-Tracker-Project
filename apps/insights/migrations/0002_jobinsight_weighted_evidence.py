"""Add weighted evidence storage to generated job insights."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("insights", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobinsight",
            name="missing_weighted_target_terms",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="jobinsight",
            name="top_overlapping_weighted_terms",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
