"""
Migration to update ShareLink model:
- Remove token UUID field (no longer needed - tokens are stateless)
- Remove max_downloads field (no longer needed - unlimited downloads)
- Remove current_downloads field (no longer needed - stateless)
- Add created_at field for audit trails
"""

from django.db import migrations, models
import django.db.models.deletion
import django.conf


class Migration(migrations.Migration):

    dependencies = [
        ("files", "0001_initial"),
    ]

    operations = [
        # First remove old fields
        migrations.RemoveField(
            model_name='sharelink',
            name='token',
        ),
        migrations.RemoveField(
            model_name='sharelink',
            name='max_downloads',
        ),
        migrations.RemoveField(
            model_name='sharelink',
            name='current_downloads',
        ),
        # Add new created_at field with default
        migrations.AddField(
            model_name='sharelink',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        # Alter field to ensure proper constraints
        migrations.AlterField(
            model_name='sharelink',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
