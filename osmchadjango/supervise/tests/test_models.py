from django.test import TestCase
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.db.utils import IntegrityError

from ...changeset.tests.modelfactories import ChangesetFactory, UserFactory
from ..models import AreaOfInterest


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
            filters={'editor__icontains': 'Potlatch 2', 'harmful': 'False'},
            geometry=self.m_polygon
            )
        self.area_2 = AreaOfInterest.objects.create(
            user=self.user,
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
            '{} - {}'.format(self.area.id, self.area.name)
            )

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
                geometry=self.m_polygon
                )

    def test_changesets_method(self):
        ChangesetFactory(bbox=Polygon(((10, 10), (10, 11), (11, 11), (10, 10))))
        # changeset created by the same user of the AreaOfInterest
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
