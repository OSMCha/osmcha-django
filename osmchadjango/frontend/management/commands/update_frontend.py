import tempfile
import shutil
from os.path import join
from os import listdir

from django.core.management.base import BaseCommand
from django.conf import settings

import git


class Command(BaseCommand):
    help = """Access the osmcha-frontend repository and update the frontend
    templates and static files.
    """

    def handle(self, *args, **options):
        temp_dir = tempfile.mkdtemp()
        static_dir = settings.STATICFILES_DIRS[0]
        templates_dir = join(
            settings.APPS_DIR.root, 'frontend', 'templates', 'frontend'
            )
        repo = git.Repo.clone_from(
            'https://github.com/mapbox/osmcha-frontend.git',
            temp_dir,
            branch=settings.OSMCHA_FRONTEND_VERSION,
            depth=1
            )
        print('Cloned osmcha-frontend ({}) to {}'.format(repo.commit().hexsha, temp_dir))

        main_files = [
            'service-worker.js', 'manifest.json', 'asset-manifest.json',
            'favicon.ico'
            ]
        for file in main_files:
            shutil.copyfile(join(temp_dir, file), join(static_dir, file))

        static_files = [
            join('css', f)
            for f in listdir(join(temp_dir, 'static', 'css'))
            ]
        static_files += [
            join('js', f)
            for f in listdir(join(temp_dir, 'static', 'js'))
            ]
        static_files += [
            join('media', f)
            for f in listdir(join(temp_dir, 'static', 'media'))
            ]

        for file in static_files:
            shutil.copyfile(
                join(temp_dir, 'static', file),
                join(static_dir, file)
                )

        html_files = [f for f in listdir(temp_dir) if f.endswith('.html')]
        for file in html_files:
            shutil.copyfile(join(temp_dir, file), join(templates_dir, file))
