from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

import dashapp.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dashapp', '0003_merge_20260708_1056'),
    ]

    operations = [
        migrations.CreateModel(
            name='UploadedDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('category', models.CharField(choices=[('report', 'Report'), ('minutes', 'Minutes'), ('policy', 'Policy'), ('other', 'Other')], default='report', max_length=20)),
                ('description', models.TextField(blank=True)),
                ('file', models.FileField(upload_to=dashapp.models.document_upload_path)),
                ('original_filename', models.CharField(max_length=255)),
                ('file_size', models.PositiveIntegerField(default=0)),
                ('visibility', models.CharField(choices=[('all', 'All workers'), ('managers', 'Managers and admins'), ('private', 'Uploader only')], default='all', max_length=20)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='uploaded_documents', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-uploaded_at'],
                'indexes': [
                    models.Index(fields=['category'], name='dashapp_upl_categor_ea844d_idx'),
                    models.Index(fields=['visibility'], name='dashapp_upl_visibil_ee1018_idx'),
                    models.Index(fields=['uploaded_at'], name='dashapp_upl_uploade_4d7e0e_idx'),
                ],
            },
        ),
    ]
