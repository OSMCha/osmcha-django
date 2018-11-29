from datetime import datetime

from django.test import TestCase
from django.contrib.gis.geos import MultiPolygon, Polygon, Point, LineString
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from ...changeset.tests.modelfactories import ChangesetFactory, UserFactory
from ..models import AreaOfInterest, BlacklistedUser


class TestAreaOfInterestModel(TestCase):
    def setUp(self):
        self.m_polygon = MultiPolygon(
            Polygon(((0, 0), (0, 1), (1, 1), (0, 0))),
            Polygon(((1, 1), (1, 2), (2, 2), (1, 1)))
            )
        self.m_polygon_2 = MultiPolygon(
            Polygon(((30, 30), (30, 31), (31, 31), (30, 30))),
            Polygon(((31, 31), (31, 32), (32, 32), (31, 31)))
            )
        self.user = UserFactory()
        self.area = AreaOfInterest.objects.create(
            name='Best place in the world',
            user=self.user,
            filters={
                'editor': 'Potlatch 2',
                'harmful': 'False',
                'geometry': self.m_polygon.geojson
                },
            geometry=self.m_polygon
            )
        self.area_2 = AreaOfInterest.objects.create(
            user=self.user,
            filters={'geometry': self.m_polygon_2.geojson},
            geometry=self.m_polygon_2
            )
        self.area_3 = AreaOfInterest.objects.create(
            user=self.user,
            name='Harmful edits',
            filters={'harmful': 'False'},
            )

    def test_creation(self):
        self.assertEqual(AreaOfInterest.objects.count(), 3)
        self.assertEqual(
            self.area.__str__(),
            '{} by {}'.format(self.area.name, self.area.user.username)
            )

    def test_auto_date_field(self):
        self.assertIsNotNone(self.area.date)
        self.assertIsNotNone(self.area_2.date)
        self.assertIsNotNone(self.area_3.date)

    def test_ordering(self):
        areas = AreaOfInterest.objects.all()
        self.assertEqual(areas[0], self.area_3)
        self.assertEqual(areas[1], self.area_2)
        self.assertEqual(areas[2], self.area)

    def test_unique_name_for_user(self):
        with self.assertRaises(IntegrityError):
            AreaOfInterest.objects.create(
                user=self.user,
                name='Best place in the world',
                geometry=self.m_polygon
                )

    def test_required_user_field(self):
        with self.assertRaises(IntegrityError):
            AreaOfInterest.objects.create(
                filters={'geometry': self.m_polygon.geojson},
                geometry=self.m_polygon
                )

    def test_required_filters_field(self):
        with self.assertRaises(IntegrityError):
            AreaOfInterest.objects.create(
                user=self.user,
                name='New filter'
                )

    def test_changesets_method(self):
        ChangesetFactory(bbox=Polygon(((10, 10), (10, 11), (11, 11), (10, 10))))
        ChangesetFactory(
            editor='JOSM 1.5',
            harmful=False,
            bbox=Polygon(((0, 0), (0, 0.5), (0.7, 0.5), (0, 0))),
            )
        ChangesetFactory(
            harmful=True,
            bbox=Polygon(((0, 0), (0, 0.5), (0.7, 0.5), (0, 0))),
            )
        changeset = ChangesetFactory(
            id=31982804,
            harmful=False,
            bbox=Polygon(((0, 0), (0, 0.5), (0.7, 0.5), (0, 0))),
            )

        self.assertEqual(self.area.changesets().count(), 1)
        self.assertIn(changeset, self.area.changesets())
        self.assertEqual(self.area_2.changesets().count(), 0)
        self.assertEqual(self.area_3.changesets().count(), 2)

    def test_other_geometry_types(self):
        ChangesetFactory(bbox=Polygon(((10, 10), (10, 11), (11, 11), (10, 10))))
        ChangesetFactory(
            editor='JOSM 1.5',
            harmful=False,
            bbox=Polygon(((0, 0), (0, 0.5), (0.7, 0.5), (0, 0))),
            )

        point = Point((0.5, 0.5))
        point_aoi = AreaOfInterest.objects.create(
            name='Point filter',
            user=self.user,
            filters={
                'geometry': point.geojson
                },
            geometry=point
            )
        self.assertEqual(point_aoi.changesets().count(), 1)

        line = LineString(((0.5, 0.5), (1, 1)))
        line_aoi = AreaOfInterest.objects.create(
            name='Line filter',
            user=self.user,
            filters={
                'geometry': line.geojson
                },
            geometry=line
            )
        self.assertEqual(line_aoi.changesets().count(), 1)

        polygon = Polygon(((0, 0), (0, 0.5), (0.7, 0.5), (0, 0)))
        polygon_aoi = AreaOfInterest.objects.create(
            name='Polygon filter',
            user=self.user,
            filters={
                'geometry': polygon.geojson
                },
            geometry=polygon
            )
        self.assertEqual(polygon_aoi.changesets().count(), 1)

        self.assertEqual(AreaOfInterest.objects.count(), 6)


class TestBlacklistedUserModel(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.other_user = UserFactory()
        self.blacklisted = BlacklistedUser.objects.create(
            username='Bad User',
            uid='3434',
            added_by=self.user,
            )

    def test_creation(self):
        self.assertEqual(BlacklistedUser.objects.count(), 1)
        self.assertEqual(self.blacklisted.__str__(), '3434')
        self.assertIsInstance(self.blacklisted.date, datetime)

    def test_validation(self):
        with self.assertRaises(ValidationError):
            BlacklistedUser.objects.create(
                added_by=self.user,
                )
        with self.assertRaises(ValidationError):
            BlacklistedUser.objects.create(
                username='Other User',
                )
        with self.assertRaises(ValidationError):
            BlacklistedUser.objects.create(
                username='Other User',
                uid='3434',
                added_by=self.user,
                )
        with self.assertRaises(ValidationError):
            BlacklistedUser.objects.create(
                uid='5643',
                added_by=self.user,
                )

        BlacklistedUser.objects.create(
            username='Bad User',
            uid='5643',
            added_by=self.user,
            )
        BlacklistedUser.objects.create(
            username='Bad User',
            uid='5643',
            added_by=self.other_user,
            )
        self.assertEqual(BlacklistedUser.objects.count(), 3)
