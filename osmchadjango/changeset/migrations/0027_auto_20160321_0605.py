# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0026_auto_20160314_1227'),
    ]

    operations = [
        migrations.CreateModel(
            name='SuspicionScore',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.IntegerField()),
                ('reason', models.CharField(max_length=255)),
                ('changeset', models.ForeignKey(to='changeset.Changeset', on_delete=models.deletion.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='UserSuspicionScore',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.IntegerField()),
                ('reason', models.CharField(max_length=255)),
                ('user', models.ForeignKey(to='changeset.UserDetail', on_delete=models.deletion.CASCADE)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='usersuspicionscore',
            unique_together=set([('user', 'score', 'reason')]),
        ),
        migrations.AlterUniqueTogether(
            name='suspicionscore',
            unique_together=set([('changeset', 'score', 'reason')]),
        ),
    ]
