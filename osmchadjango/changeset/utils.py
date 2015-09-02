# -*- coding: utf-8 -*-
from osmcha.changeset import Analyse

from os.path import join

from .models import Changeset, SuspicionReasons


def format_url(n):
    n = str(n)
    base_url = 'http://planet.openstreetmap.org/replication/changesets/'
    return join(base_url, '00%s' % n[0], n[1:4], '%s.osm.gz' % n[4:])


def create_changeset(changeset_id):
    ch = Analyse(changeset_id)
    ch.full_analysis()

    # remove suspicion_reasons and empty values from dict
    ch_dict = ch.__dict__.copy()
    for key in ch.__dict__:
        if ch.__dict__.get(key) == '':
            ch_dict.pop(key)
    ch_dict.pop('suspicion_reasons')

    #save changeset
    changeset = Changeset(**ch_dict)
    changeset.save()

    if ch.suspicion_reasons:
        for reason in ch.suspicion_reasons:
            reason, created = SuspicionReasons.objects.get_or_create(name=reason)
            reason.changesets.add(changeset)

    print('{c[id]} created'.format(c=ch_dict))