from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CompressedPDF',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original_name', models.CharField(max_length=255)),
                ('status', models.CharField(default='PENDING', max_length=15)),
                ('storage_path', models.CharField(max_length=500)),
                ('supabase_url', models.URLField(blank=True, null=True)),
                ('original_size', models.BigIntegerField()),
                ('compressed_size', models.BigIntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, to='users.customuser')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='ShareLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.UUIDField(default=uuid.uuid4, unique=True, editable=False)),
                ('expires_at', models.DateTimeField()),
                ('max_downloads', models.IntegerField(default=100)),
                ('current_downloads', models.IntegerField(default=0)),
                ('pdf_record', models.ForeignKey(on_delete=models.deletion.CASCADE, to='files.compressedpdf')),
            ],
        ),
    ]
