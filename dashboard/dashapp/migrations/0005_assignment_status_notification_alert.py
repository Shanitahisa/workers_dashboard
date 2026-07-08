from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashapp', '0004_uploadeddocument'),
    ]

    operations = [
        migrations.AddField(
            model_name='actionpointassignment',
            name='postponed_until',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='actionpointassignment',
            name='status',
            field=models.CharField(
                choices=[
                    ('active', 'Active'),
                    ('done', 'Done'),
                    ('postponed', 'Postponed'),
                ],
                default='active',
                max_length=20,
            ),
        ),
    ]
