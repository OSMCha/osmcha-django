# -*- coding: utf-8 -*-
from __future__ import print_function

from celery import shared_task, group
import yaml
from osmcha.changeset import Analyse, ChangesetList

import requests
from os.path import join

from django.conf import settings

from .models import Changeset, SuspicionReasons, Import


@shared_task
def create_changeset(changeset_id):
    """Analyse and create the changeset in the database."""
    ch = Analyse(changeset_id)
    ch.full_analysis()

    # remove suspicion_reasons and empty values from dict
    ch_dict = ch.__dict__.copy()
    for key in ch.__dict__:
        if ch.__dict__.get(key) == '':
            ch_dict.pop(key)

    ch_dict['score'] = ch_dict['changeset_score']
    ch_dict.pop('suspicion_reasons')
    ch_dict.pop('user_details')
    ch_dict.pop('user_score')
    ch_dict.pop('changeset_score')
    ch_dict.pop('user_score_details')
    ch_dict.pop('changeset_score_details')

    # save changeset
    changeset, created = Changeset.objects.update_or_create(id=ch_dict['id'], defaults=ch_dict)

    if ch.suspicion_reasons:
        for reason in ch.suspicion_reasons:
            reason, created = SuspicionReasons.objects.get_or_create(name=reason)
            reason.changesets.add(changeset)

    SuspicionScore.objects.filter(changeset=changeset).delete()
    for detail in ch.changeset_score_details:
        s = SuspicionScore(changeset=changeset)
        s.score = detail['score']
        s.reason = detail['reason']
        s.save()

    if ch.user_details:
        changeset.save_user_details(ch)

    print('{c[id]} created'.format(c=ch_dict))


@shared_task
def get_filter_changeset_file(url, geojson_filter=settings.CHANGESETS_FILTER):
    """Filter the changesets of the replication file by the area defined in the
    GeoJSON file.
    """
    cl = ChangesetList(url, geojson_filter)
    group(create_changeset.s(c['id']) for c in cl.changesets)()


def format_url(n):
    """Return the url of a replication file."""
    n = str(n)
    base_url = 'http://planet.openstreetmap.org/replication/changesets/'
    return join(base_url, '00%s' % n[0], n[1:4], '%s.osm.gz' % n[4:])


@shared_task
def import_replications(start, end):
    """Recieves a start and a end number and import each replication file in
    this interval.
    """
    Import(start=start, end=end).save()
    urls = [format_url(n) for n in range(start, end + 1)]
    group(get_filter_changeset_file.s(url) for url in urls)()


def get_last_replication_id():
    """Get the id number of the last replication file available on Planet OSM.
    """
    state = requests.get(
        'http://planet.openstreetmap.org/replication/changesets/state.yaml'
        ).content
    state = yaml.load(state)
    return state.get('sequence')


@shared_task
def fetch_latest():
    """Function to import all the replication files since the last import or the
    last 1000.
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
