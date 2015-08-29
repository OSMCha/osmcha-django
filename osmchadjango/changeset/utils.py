# -*- coding: utf-8 -*-
from osmcha.changeset import Analyse

from .models import Changeset, SuspicionReasons


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