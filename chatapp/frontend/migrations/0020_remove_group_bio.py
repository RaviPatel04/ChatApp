# Generated by Django 5.1.6 on 2025-04-02 05:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0019_group_bio'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='group',
            name='bio',
        ),
    ]
