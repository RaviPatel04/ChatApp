# Generated by Django 5.1.6 on 2025-04-11 12:47

import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0027_alter_profile_avatar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupprofile',
            name='group_avatar',
            field=cloudinary.models.CloudinaryField(default='group_avatars/group_default', max_length=255, verbose_name='image'),
        ),
    ]
