import json
from os.path import join
import requests

from django.conf import settings


def remove_unneeded_properties(feature):
    keys_to_remove = [
        key for key in feature['properties'].keys()
        if key.startswith('osm:') or key.startswith('result:')
        ]
    for key in keys_to_remove:
        feature['properties'].pop(key)

    if feature['properties'].get('oldVersion'):
        feature['properties'].pop('oldVersion')
    if feature['properties'].get('suspicions'):
        feature['properties'].pop('suspicions')

    return feature


def format_challenge_task_payload(feature, challenge_id, name, reasons=[]):
    if len(reasons):
        feature['properties']['osmcha_reasons'] = ", ".join([i for i in reasons])
    payload = {
        "parent": challenge_id,
        "name": "{}".format(name),
        "geometries": {"features": [remove_unneeded_properties(feature)]}
        }
    return json.dumps(payload)


def push_feature_to_maproulette(feature, challenge_id, name, reasons=[]):
    if (settings.MAP_ROULETTE_API_KEY is not None and
            settings.MAP_ROULETTE_API_URL is not None):
        payload = format_challenge_task_payload(
            feature, challenge_id, name, reasons
            )
        headers = {
            "Content-Type": "application/json",
            "apiKey": settings.MAP_ROULETTE_API_KEY
            }
        return requests.post(
            join(settings.MAP_ROULETTE_API_URL, 'task'),
            headers=headers,
            data=payload
            )
