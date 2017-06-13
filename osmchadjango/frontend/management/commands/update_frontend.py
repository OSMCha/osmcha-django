import tempfile
import shutil
from os.path import join

from django.core.management.base import BaseCommand
from django.conf import settings

import git


class Command(BaseCommand):
    help = """Access the osmcha-frontend repository and update the frontend
    files.
    """

    def handle(self, *args, **options):
        temp_dir = tempfile.mkdtemp()
        static_dir = settings.STATICFILES_DIRS[0]
        repo = git.Repo.clone_from(
            'git@github.com:mapbox/osmcha-frontend.git',
            temp_dir,
            branch='gh-pages'
            )
        print('Cloned osmcha-frontend ({}) to {}'.format(repo.commit().hexsha, temp_dir))

        static_files = ['service-worker.js', 'manifest.json', 'asset-manifest.json']
        for file in static_files:
            shutil.copyfile(join(temp_dir, file), join(static_dir, file))
