# Generated by Django 3.1.4 on 2021-01-27 11:58

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('correspondence', '0008_auto_20210127_1026'),
    ]

    operations = [
        migrations.AddField(
            model_name='radicate',
            name='actual_user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='radicates_user', to='correspondence.person'),
        ),
        migrations.AlterField(
            model_name='radicate',
            name='creator',
            field=models.ForeignKey(default=False, on_delete=django.db.models.deletion.CASCADE, related_name='radicates_creator', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='radicate',
            name='person',
            field=models.ForeignKey(default=False, on_delete=django.db.models.deletion.CASCADE, related_name='radicates_person', to='correspondence.person'),
        ),
    ]
