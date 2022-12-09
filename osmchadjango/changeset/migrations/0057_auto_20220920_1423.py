# Generated by Django 2.2.28 on 2022-09-20 14:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0056_auto_20220429_1305'),
    ]

    operations = [
        migrations.AlterField(
            model_name='changeset',
            name='checked',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='comment',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='comments_count',
            field=models.IntegerField(default=0, null=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='create',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='delete',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='editor',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='harmful',
            field=models.NullBooleanField(),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='imagery_used',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='is_suspect',
            field=models.BooleanField(),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='modify',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='source',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='changeset',
            name='uid',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='User ID'),
        ),
    ]