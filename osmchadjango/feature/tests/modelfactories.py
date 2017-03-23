import json
from datetime import datetime

from django.contrib.gis.geos import Point, LineString

import factory

from ...changeset.tests.modelfactories import ChangesetFactory, UserFactory
from ..models import Feature


class FeatureFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Feature

    changeset = factory.SubFactory(ChangesetFactory)
    osm_id = factory.Sequence(lambda n: '%d' % n)
    osm_type = 'node'
    osm_version = 1
    geometry = Point(42.1, 13.4)
    geojson = json.dumps({'properties': [{'osm:type': 'node'}]})


class CheckedFeatureFactory(FeatureFactory):
    checked = True
    check_user = factory.SubFactory(UserFactory)
    check_date = factory.LazyFunction(datetime.now)


class WayFeatureFactory(FeatureFactory):
    osm_id = 323432
    osm_type = 'way'
    geometry = LineString([(42.1, 13.4), (42.2, 14)])
    geojson = json.dumps({'properties': [{'osm:type': 'way'}]})
