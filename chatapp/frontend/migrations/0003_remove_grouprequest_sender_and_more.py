# Generated by Django 5.1.6 on 2025-03-27 07:05

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0002_grouprequest'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='grouprequest',
            name='sender',
        ),
        migrations.RemoveField(
            model_name='grouprequest',
            name='updated_at',
        ),
        migrations.AddField(
            model_name='grouprequest',
            name='invited_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='received_group_requests', to=settings.AUTH_USER_MODEL),
        ),
    ]
