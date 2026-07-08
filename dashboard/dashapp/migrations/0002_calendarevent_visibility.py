from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='calendarevent',
            name='visibility',
            field=models.CharField(
                choices=[('public', 'Public'), ('private', 'Private')],
                default='public',
                max_length=20,
            ),
        ),
    ]
