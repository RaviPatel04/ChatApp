# Generated by Django 5.1.6 on 2025-04-11 10:55

import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0024_alter_message_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupmessage',
            name='file',
            field=cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True, verbose_name='file'),
        ),
    ]
