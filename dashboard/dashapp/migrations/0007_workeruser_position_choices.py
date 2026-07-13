from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashapp', '0006_merge_20260708_1300'),
    ]

    operations = [
        migrations.AddField(
            model_name='workeruser',
            name='position_other',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AlterField(
            model_name='workeruser',
            name='position',
            field=models.CharField(
                choices=[
                    ('admin', 'Admin'),
                    ('ict_assistant', 'ICT Assistant'),
                    ('legal', 'Legal'),
                    ('secretary_general', 'Secretary General'),
                    ('other', 'Other'),
                ],
                max_length=40,
            ),
        ),
    ]
