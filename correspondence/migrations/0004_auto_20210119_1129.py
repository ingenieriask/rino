# Generated by Django 3.1.4 on 2021-01-19 16:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('correspondence', '0003_auto_20210113_1034'),
    ]

    operations = [
        migrations.AlterField(
            model_name='radicate',
            name='document_file',
            field=models.FileField(default='uploads/blank.pdf', upload_to='uploads/'),
        ),
    ]
