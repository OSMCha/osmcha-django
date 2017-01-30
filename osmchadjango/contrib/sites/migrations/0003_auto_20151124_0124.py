# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.sites.models


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0002_set_site_domain_and_name'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='site',
            managers=[
                ('objects', django.contrib.sites.models.SiteManager()),
            ],
        ),
    ]
