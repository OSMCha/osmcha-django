# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('changeset', '0011_import'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserWhitelist',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('whitelist_user', models.CharField(max_length=1000)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.deletion.SET_NULL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='userwhitelist',
            unique_together=set([('user', 'whitelist_user')]),
        ),
    ]
