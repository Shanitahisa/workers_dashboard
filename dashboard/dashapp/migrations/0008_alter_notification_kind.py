from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashapp', '0007_workeruser_position_choices'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='kind',
            field=models.CharField(
                choices=[
                    ('assignment', 'Assignment'),
                    ('progress', 'Progress Update'),
                    ('comment', 'Comment'),
                    ('event', 'Event'),
                    ('reminder', 'Reminder'),
                    ('alert', 'Alert'),
                ],
                max_length=20,
            ),
        ),
    ]
