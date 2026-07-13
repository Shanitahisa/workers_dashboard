from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashapp', '0009_calendarevent_owner'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calendarevent',
            name='recurrence',
            field=models.CharField(
                choices=[
                    ('none', 'No repeat'),
                    ('daily', 'Daily'),
                    ('weekly', 'Weekly'),
                    ('monthly', 'Monthly'),
                    ('yearly', 'Yearly'),
                ],
                default='none',
                max_length=20,
            ),
        ),
    ]
