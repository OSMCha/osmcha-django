# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from os.path import join
from urllib.parse import quote
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from django.conf import settings

import requests
from requests_oauthlib import OAuth1Session
from osmcha.changeset import Analyse, ChangesetList

from .models import Changeset, SuspicionReasons, Import


def create_changeset(changeset_id):
    """Analyse and create the changeset in the database."""
    ch = Analyse(changeset_id)
    ch.full_analysis()

    # remove suspicion_reasons
    ch_dict = ch.get_dict()
    ch_dict.pop('suspicion_reasons')

    # remove bbox field if it is not a valid geometry
    if ch.bbox == 'GEOMETRYCOLLECTION EMPTY':
        ch_dict.pop('bbox')

    # save changeset.
    changeset, created = Changeset.objects.update_or_create(
        id=ch_dict['id'],
        defaults=ch_dict
        )

    if ch.suspicion_reasons:
        for reason in ch.suspicion_reasons:
            reason, created = SuspicionReasons.objects.get_or_create(name=reason)
            reason.changesets.add(changeset)

    print('{c[id]} created'.format(c=ch_dict))
    return changeset


def get_filter_changeset_file(url, geojson_filter=settings.CHANGESETS_FILTER):
    """Filter changesets from a replication file by the area defined in the
    GeoJSON file.
    """
    cl = ChangesetList(url, geojson_filter)
    for c in cl.changesets:
        print('Creating changeset {}'.format(c['id']))
        create_changeset(c['id'])


def format_url(n):
    """Return the URL of a replication file."""
    n = str(n)
    return join(settings.OSM_PLANET_BASE_URL, '00%s' % n[0], n[1:4], '%s.osm.gz' % n[4:])


def import_replications(start, end):
    """Recieves a start and an end number, and import each replication file in
    this interval.
    """
    Import(start=start, end=end).save()
    urls = [format_url(n) for n in range(start, end + 1)]
    for url in urls:
        print('Importing {}'.format(url))
        get_filter_changeset_file(url)


def get_last_replication_id():
    """Get the id of the last replication file available on Planet OSM.
    """
    state = requests.get(
        '{}state.yaml'.format(settings.OSM_PLANET_BASE_URL)
        ).content
    state = yaml.load(state, Loader)
    return state.get('sequence')


def fetch_latest():
    """Function to import all the replication files since the last import or the
    last 1000.
    FIXME: define error in except line
    """
    try:
        last_import = Import.objects.all().order_by('-end')[0].end
    except:
        last_import = None

    sequence = get_last_replication_id()

    if last_import:
        start = last_import + 1
    else:
        start = sequence - 1000
    print("Importing replications from %d to %d" % (start, sequence,))
    import_replications(start, sequence)


class ChangesetCommentAPI(object):
    """Class that allows us to publish comments in changesets on the
    OpenStreetMap website.
    """
    def __init__(self, user, changeset_id):
        self.changeset_id = changeset_id
        user_token = user.social_auth.all().first().access_token
        self.client = OAuth1Session(
            settings.SOCIAL_AUTH_OPENSTREETMAP_KEY,
            client_secret=settings.SOCIAL_AUTH_OPENSTREETMAP_SECRET,
            resource_owner_key=user_token['oauth_token'],
            resource_owner_secret=user_token['oauth_token_secret']
            )
        self.url = '{}/api/0.6/changeset/{}/comment/'.format(
            settings.OSM_SERVER_URL,
            changeset_id
            )

    def post_comment(self, message=None):
        """Post comment to changeset."""
        response = self.client.post(
            self.url,
            data='text={}'.format(quote(message)).encode("utf-8")
            )
        if response.status_code == 200:
            print(
                'Comment in the changeset {} posted successfully.'.format(
                    self.changeset_id
                    )
                )
            return {'success': True}
        else:
            print("""Some error occurred and it wasn't possible to post the
                comment to the changeset {}.""".format(self.changeset_id))
            return {'success': False}
