from django.db import migrations

def replace_null_by_zero(apps, schema_editor):
    Changeset = apps.get_model('changeset', 'Changeset')
    Changeset.objects.filter(comments_count=None).update(comments_count=0)

class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0052_changeset_comments_count'),
    ]

    operations = [
        migrations.RunPython(replace_null_by_zero),
    ]
