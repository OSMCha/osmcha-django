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
    osm_id = factory.Sequence(lambda n: n)
    osm_type = 'node'
    url = factory.Sequence(lambda n: 'node-%d' % n)
    osm_version = 1
    geometry = Point(42.1, 13.4)
    geojson = json.dumps({'properties': [{'osm:type': 'node'}]})


class CheckedFeatureFactory(FeatureFactory):
    checked = True
    harmful = True
    check_user = factory.SubFactory(UserFactory)
    check_date = factory.LazyFunction(datetime.now)
    osm_version = 2


class WayFeatureFactory(FeatureFactory):
    osm_version = 3
    osm_type = 'way'
    url = factory.Sequence(lambda n: 'way-%d' % n)
    geometry = LineString([(42.1, 13.4), (42.2, 14)])
    geojson = json.dumps({'properties': [{'osm:type': 'way'}]})
