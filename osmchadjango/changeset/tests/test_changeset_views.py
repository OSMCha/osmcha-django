import json

from django.contrib.gis.geos import Polygon
from django.core.urlresolvers import reverse

from social_django.models import UserSocialAuth
from rest_framework.test import APITestCase

from ...users.models import User
from ...feature.tests.modelfactories import FeatureFactory
from ..models import SuspicionReasons, Tag, Changeset
from ..views import ChangesetListAPIView, PaginatedCSVRenderer
from .modelfactories import (
    ChangesetFactory, SuspectChangesetFactory, GoodChangesetFactory,
    HarmfulChangesetFactory, TagFactory, UserWhitelistFactory
    )


class TestChangesetListView(APITestCase):

    def setUp(self):
        SuspectChangesetFactory.create_batch(26)
        ChangesetFactory.create_batch(26)
        self.url = reverse('changeset:list')

    def test_changeset_list_response(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['features']), 50)
        self.assertEqual(response.data['count'], 52)

    def test_pagination(self):
        response = self.client.get(self.url, {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['features']), 2)
        self.assertEqual(response.data['count'], 52)
        # test page_size parameter
        response = self.client.get(self.url, {'page_size': 60})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['features']), 52)

    def test_filters(self):
        response = self.client.get(self.url, {'in_bbox': '-72,43,-70,45'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 52)

        response = self.client.get(self.url, {'in_bbox': '-3.17,-91.98,-2.1,-90.5'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        response = self.client.get(self.url, {'is_suspect': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 26)

        response = self.client.get(self.url, {'is_suspect': 'false'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 26)

    def test_area_lt_filter(self):
        """Test in_bbox in combination with area_lt filter field."""
        ChangesetFactory(
            bbox=Polygon([(0, 0), (0, 3), (3, 3), (3, 0), (0, 0)])
            )
        response = self.client.get(self.url, {'in_bbox': '0,0,1,1', 'area_lt': 10})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

        response = self.client.get(self.url, {'in_bbox': '0,0,1,1', 'area_lt': 8})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        response = self.client.get(self.url, {'in_bbox': '0,0,2,2', 'area_lt': 3})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

        response = self.client.get(self.url, {'in_bbox': '0,0,2,2', 'area_lt': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

    def test_hide_whitelist_filter(self):
        user = User.objects.create_user(
            username='test_user',
            email='b@a.com',
            password='password'
            )
        UserSocialAuth.objects.create(
            user=user,
            provider='openstreetmap',
            uid='123123',
            )
        UserWhitelistFactory(user=user, whitelist_user='test')

        # test without login
        response = self.client.get(self.url, {'hide_whitelist': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 52)
        response = self.client.get(
            self.url,
            {'hide_whitelist': 'true', 'checked': 'true'}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        # test with login. As all changesets in the DB are from a whitelisted
        # user, the features count will be zero
        self.client.login(username=user.username, password='password')
        response = self.client.get(self.url, {'hide_whitelist': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

    def test_csv_renderer(self):
        self.assertIn(
            PaginatedCSVRenderer,
            ChangesetListAPIView().renderer_classes
            )
        response = self.client.get(self.url, {'format': 'csv', 'page_size': 60})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['features']), 52)
        response = self.client.get(
            self.url,
            {'is_suspect': 'true', 'format': 'csv'}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['features']), 26)


class TestChangesetFilteredViews(APITestCase):
    def setUp(self):
        ChangesetFactory()
        SuspectChangesetFactory()
        HarmfulChangesetFactory()
        GoodChangesetFactory()

    def test_suspect_changesets_view(self):
        url = reverse('changeset:suspect-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)

    def test_no_suspect_changesets_view(self):
        url = reverse('changeset:no-suspect-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_harmful_changesets_view(self):
        url = reverse('changeset:harmful-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_no_harmful_changesets_view(self):
        url = reverse('changeset:no-harmful-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_checked_changesets_view(self):
        url = reverse('changeset:checked-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)

    def test_unchecked_changesets_view(self):
        url = reverse('changeset:unchecked-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)


class TestChangesetListViewOrdering(APITestCase):

    def setUp(self):
        SuspectChangesetFactory.create_batch(2, delete=2)
        HarmfulChangesetFactory.create_batch(24, form_create=20, modify=2, delete=40)
        GoodChangesetFactory.create_batch(24, form_create=1000, modify=20)
        self.url = reverse('changeset:list')

    def test_ordering(self):
        # default ordering is by descending id
        response = self.client.get(self.url)
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.all()]
            )
        # ascending id
        response = self.client.get(self.url, {'order_by': 'id'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('id')]
            )
        # ascending date ordering
        response = self.client.get(self.url, {'order_by': 'date'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('date')]
            )
        # descending date ordering
        response = self.client.get(self.url, {'order_by': '-date'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('-date')]
            )
        # ascending check_date
        response = self.client.get(self.url, {'order_by': 'check_date'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('check_date')]
            )
        # descending check_date ordering
        response = self.client.get(self.url, {'order_by': '-check_date'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('-check_date')]
            )
        # ascending create ordering
        response = self.client.get(self.url, {'order_by': 'create'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('create')]
            )
        # descending create ordering
        response = self.client.get(self.url, {'order_by': '-create'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('-create')]
            )
        # ascending modify ordering
        response = self.client.get(self.url, {'order_by': 'modify'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('modify')]
            )
        # descending modify ordering
        response = self.client.get(self.url, {'order_by': '-modify'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('-modify')]
            )
        # ascending delete ordering
        response = self.client.get(self.url, {'order_by': 'delete'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('delete')]
            )
        # descending delete ordering
        response = self.client.get(self.url, {'order_by': '-delete'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('-delete')]
            )

    def test_invalid_ordering_field(self):
        # default ordering is by descending id
        response = self.client.get(self.url, {'order_by': 'user'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.all()]
            )


class TestChangesetDetailView(APITestCase):

    def setUp(self):
        self.reason_1 = SuspicionReasons.objects.create(name='possible import')
        self.reason_2 = SuspicionReasons.objects.create(name='suspect word')
        self.reason_3 = SuspicionReasons.objects.create(
            name='Big edit in my city',
            is_visible=False
            )
        self.changeset = HarmfulChangesetFactory(id=31982803)
        self.feature = FeatureFactory(changeset=self.changeset)
        self.reason_1.changesets.add(self.changeset)
        self.reason_2.changesets.add(self.changeset)
        self.reason_2.features.add(self.feature)
        self.reason_3.features.add(self.feature)
        self.reason_3.changesets.add(self.changeset)
        tag = Tag.objects.create(name='Vandalism')
        tag.changesets.add(self.changeset)

    def test_changeset_detail_response(self):
        response = self.client.get(
            reverse('changeset:detail', args=[self.changeset.id])
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('id'), 31982803)
        self.assertIn('geometry', response.data.keys())
        self.assertIn('properties', response.data.keys())
        self.assertEqual(self.changeset.uid, response.data['properties']['uid'])
        self.assertEqual(
            self.changeset.editor,
            response.data['properties']['editor']
            )
        self.assertEqual(self.changeset.user, response.data['properties']['user'])
        self.assertEqual(
            self.changeset.imagery_used,
            response.data['properties']['imagery_used']
            )
        self.assertEqual(
            self.changeset.source,
            response.data['properties']['source']
            )
        self.assertEqual(
            self.changeset.comment,
            response.data['properties']['comment']
            )
        self.assertEqual(
            self.changeset.create,
            response.data['properties']['create']
            )
        self.assertEqual(
            self.changeset.modify,
            response.data['properties']['modify']
            )
        self.assertEqual(
            self.changeset.delete,
            response.data['properties']['delete']
            )
        self.assertEqual(
            self.changeset.check_user.name,
            response.data['properties']['check_user']
            )
        self.assertTrue(response.data['properties']['is_suspect'])
        self.assertTrue(response.data['properties']['checked'])
        self.assertTrue(response.data['properties']['harmful'])
        self.assertIn('date', response.data['properties'].keys())
        self.assertIn('check_date', response.data['properties'].keys())
        self.assertEqual(len(response.data['properties']['features']), 1)
        self.assertEqual(
            self.feature.osm_id,
            response.data['properties']['features'][0]['osm_id']
            )
        self.assertEqual(
            self.feature.url,
            response.data['properties']['features'][0]['url']
            )
        self.assertEqual(
            response.data['properties']['features'][0]['name'],
            'Test'
            )
        self.assertEqual(
            len(response.data['properties']['features'][0]['reasons']),
            1
            )
        self.assertIn(
            'suspect word',
            response.data['properties']['features'][0]['reasons']
            )

    def test_changeset_detail_response_with_staff_user(self):
        self.user = User.objects.create_user(
            username='test',
            password='password',
            email='a@a.com',
            is_staff=True
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='123123',
            )
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(
            reverse('changeset:detail', args=[self.changeset.id])
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(response.data['properties']['features'][0]['reasons']),
            2
            )
        self.assertIn(
            'suspect word',
            response.data['properties']['features'][0]['reasons']
            )
        self.assertIn(
            'Big edit in my city',
            response.data['properties']['features'][0]['reasons']
            )

    def test_feature_without_name_tag(self):
        self.feature.geojson = json.dumps({'properties': {'osm:type': 'node'}})
        self.feature.save()
        response = self.client.get(
            reverse('changeset:detail', args=[self.changeset.id])
            )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(
            response.data['properties']['features'][0]['name']
            )


class TestReasonsAndTagFieldsInChangesetViews(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test',
            password='password',
            email='a@a.com',
            is_staff=True
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='123123',
            )
        self.reason_1 = SuspicionReasons.objects.create(name='possible import')
        self.reason_2 = SuspicionReasons.objects.create(name='suspect word')
        self.reason_3 = SuspicionReasons.objects.create(
            name='Big edit in my city',
            is_visible=False
            )
        self.changeset = HarmfulChangesetFactory(id=31982803)
        self.reason_1.changesets.add(self.changeset)
        self.reason_2.changesets.add(self.changeset)
        self.reason_3.changesets.add(self.changeset)
        self.tag_1 = Tag.objects.create(name='Vandalism')
        self.tag_2 = Tag.objects.create(
            name='Vandalism in my city',
            is_visible=False
            )
        self.tag_1.changesets.add(self.changeset)
        self.tag_2.changesets.add(self.changeset)

    def test_detail_view_by_normal_user(self):
        response = self.client.get(reverse('changeset:detail', args=[self.changeset.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['properties']['reasons']), 2)
        self.assertEqual(len(response.data['properties']['tags']), 1)
        self.assertIn('possible import', response.data['properties']['reasons'])
        self.assertIn('suspect word', response.data['properties']['reasons'])
        self.assertIn(
            'Vandalism',
            response.data['properties']['tags']
            )

    def test_detail_view_by_admin(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(reverse('changeset:detail', args=[self.changeset.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Big edit in my city',
            response.data['properties']['reasons']
            )
        self.assertEqual(len(response.data['properties']['reasons']), 3)
        self.assertEqual(len(response.data['properties']['tags']), 2)
        self.assertIn(
            'Vandalism in my city',
            response.data['properties']['tags']
            )
        self.assertEqual(response.data.get('id'), 31982803)
        self.assertIn('geometry', response.data.keys())
        self.assertIn('properties', response.data.keys())
        self.assertEqual(self.changeset.uid, response.data['properties']['uid'])
        self.assertEqual(
            self.changeset.editor,
            response.data['properties']['editor']
            )
        self.assertEqual(self.changeset.user, response.data['properties']['user'])
        self.assertEqual(
            self.changeset.imagery_used,
            response.data['properties']['imagery_used']
            )
        self.assertEqual(
            self.changeset.source,
            response.data['properties']['source']
            )
        self.assertEqual(
            self.changeset.comment,
            response.data['properties']['comment']
            )
        self.assertEqual(
            self.changeset.create,
            response.data['properties']['create']
            )
        self.assertEqual(
            self.changeset.modify,
            response.data['properties']['modify']
            )
        self.assertEqual(
            self.changeset.delete,
            response.data['properties']['delete']
            )
        self.assertEqual(
            self.changeset.check_user.name,
            response.data['properties']['check_user']
            )
        self.assertTrue(response.data['properties']['is_suspect'])
        self.assertTrue(response.data['properties']['checked'])
        self.assertTrue(response.data['properties']['harmful'])
        self.assertIn('date', response.data['properties'].keys())
        self.assertIn('check_date', response.data['properties'].keys())
        self.assertEqual(len(response.data['properties']['features']), 0)

    def test_list_view_by_normal_user(self):
        response = self.client.get(reverse('changeset:list'))
        self.assertEqual(response.status_code, 200)
        reasons = response.data['features'][0]['properties']['reasons']
        tags = response.data['features'][0]['properties']['tags']
        self.assertEqual(len(reasons), 2)
        self.assertEqual(len(tags), 1)
        self.assertIn('possible import', reasons)
        self.assertIn('suspect word', reasons)
        self.assertIn('Vandalism', tags)

    def test_list_view_by_admin(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(reverse('changeset:list'))
        self.assertEqual(response.status_code, 200)
        reasons = response.data['features'][0]['properties']['reasons']
        tags = response.data['features'][0]['properties']['tags']
        self.assertEqual(len(reasons), 3)
        self.assertEqual(len(tags), 2)
        self.assertIn('Big edit in my city', reasons)
        self.assertIn('Vandalism in my city', tags)


class TestCheckChangesetViews(APITestCase):

    def setUp(self):
        self.reason_1 = SuspicionReasons.objects.create(name='possible import')
        self.reason_2 = SuspicionReasons.objects.create(name='suspect_word')
        self.changeset = SuspectChangesetFactory(
            id=31982803, user='test', uid='123123'
            )
        self.changeset_2 = SuspectChangesetFactory(
            id=31982804, user='test2', uid='999999', editor='iD',
            )
        self.reason_1.changesets.add(self.changeset)
        self.reason_2.changesets.add(self.changeset)
        self.user = User.objects.create_user(
            username='test',
            password='password',
            email='a@a.com'
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='123123',
            )
        self.tag_1 = TagFactory(name='Illegal import')
        self.tag_2 = TagFactory(name='Vandalism')

    def test_set_harmful_changeset_unlogged(self):
        """Anonymous users can't mark a changeset as harmful."""
        response = self.client.put(
            reverse('changeset:set-harmful', args=[self.changeset])
            )
        self.assertEqual(response.status_code, 401)
        self.changeset.refresh_from_db()
        self.assertIsNone(self.changeset.harmful)
        self.assertFalse(self.changeset.checked)
        self.assertIsNone(self.changeset.check_user)
        self.assertIsNone(self.changeset.check_date)

    def test_set_good_changeset_unlogged(self):
        """Anonymous users can't mark a changeset as good."""
        response = self.client.put(
            reverse('changeset:set-good', args=[self.changeset])
            )
        self.assertEqual(response.status_code, 401)
        self.changeset.refresh_from_db()
        self.assertIsNone(self.changeset.harmful)
        self.assertFalse(self.changeset.checked)
        self.assertIsNone(self.changeset.check_user)
        self.assertIsNone(self.changeset.check_date)

    def test_set_harmful_changeset_not_allowed(self):
        """User can't mark his own changeset as harmful."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:set-harmful', args=[self.changeset])
            )
        self.assertEqual(response.status_code, 403)
        self.changeset.refresh_from_db()
        self.assertIsNone(self.changeset.harmful)
        self.assertFalse(self.changeset.checked)
        self.assertIsNone(self.changeset.check_user)
        self.assertIsNone(self.changeset.check_date)

    def test_set_good_changeset_not_allowed(self):
        """User can't mark his own changeset as good."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:set-good', args=[self.changeset])
            )
        self.assertEqual(response.status_code, 403)
        self.changeset.refresh_from_db()
        self.assertIsNone(self.changeset.harmful)
        self.assertFalse(self.changeset.checked)
        self.assertIsNone(self.changeset.check_user)
        self.assertIsNone(self.changeset.check_date)

    def test_set_harmful_changeset_get(self):
        """GET is not an allowed method in the set_harmful URL."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(
            reverse('changeset:set-harmful', args=[self.changeset_2]),
            )

        self.assertEqual(response.status_code, 405)
        self.changeset_2.refresh_from_db()
        self.assertIsNone(self.changeset_2.harmful)
        self.assertFalse(self.changeset_2.checked)
        self.assertIsNone(self.changeset_2.check_user)
        self.assertIsNone(self.changeset_2.check_date)

    def test_set_harmful_changeset_put(self):
        """User can set a changeset of another user as harmful with a PUT request.
        We can also set the tags of the changeset sending it as data.
        """
        self.client.login(username=self.user.username, password='password')
        data = {'tags': [self.tag_1.id, self.tag_2.id]}
        response = self.client.put(
            reverse('changeset:set-harmful', args=[self.changeset_2.pk]),
            data
            )

        self.assertEqual(response.status_code, 200)
        self.changeset_2.refresh_from_db()
        self.assertTrue(self.changeset_2.harmful)
        self.assertTrue(self.changeset_2.checked)
        self.assertEqual(self.changeset_2.check_user, self.user)
        self.assertIsNotNone(self.changeset_2.check_date)
        self.assertEqual(self.changeset_2.tags.count(), 2)
        self.assertIn(
            self.tag_1,
            self.changeset_2.tags.all()
            )
        self.assertIn(
            self.tag_2,
            self.changeset_2.tags.all()
            )

    def test_set_harmful_changeset_with_invalid_tag_id(self):
        """Return a 400 error if a user try to add a invalid tag id to a changeset.
        """
        self.client.login(username=self.user.username, password='password')
        data = {'tags': [self.tag_1.id, 87765, 898986]}
        response = self.client.put(
            reverse('changeset:set-harmful', args=[self.changeset_2.pk]),
            data
            )

        self.assertEqual(response.status_code, 400)
        self.changeset_2.refresh_from_db()
        self.assertIsNone(self.changeset_2.harmful)
        self.assertFalse(self.changeset_2.checked)
        self.assertIsNone(self.changeset_2.check_user)
        self.assertIsNone(self.changeset_2.check_date)
        self.assertEqual(self.changeset_2.tags.count(), 0)

    def test_set_harmful_changeset_put_without_data(self):
        """Test marking a changeset as harmful without sending data (so the
        changeset will not receive tags).
        """
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:set-harmful', args=[self.changeset_2.pk])
            )

        self.assertEqual(response.status_code, 200)
        self.changeset_2.refresh_from_db()
        self.assertTrue(self.changeset_2.harmful)
        self.assertTrue(self.changeset_2.checked)
        self.assertEqual(self.changeset_2.check_user, self.user)
        self.assertIsNotNone(self.changeset_2.check_date)
        self.assertEqual(self.changeset_2.tags.count(), 0)

    def test_set_good_changeset_get(self):
        """GET is not an allowed method in the set_good URL."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(
            reverse('changeset:set-good', args=[self.changeset_2]),
            )

        self.assertEqual(response.status_code, 405)
        self.changeset_2.refresh_from_db()
        self.assertIsNone(self.changeset_2.harmful)
        self.assertFalse(self.changeset_2.checked)
        self.assertIsNone(self.changeset_2.check_user)
        self.assertIsNone(self.changeset_2.check_date)

    def test_set_good_changeset_put(self):
        """User can set a changeset of another user as good with a PUT request.
        We can also set the tags of the changeset sending it as data.
        """
        self.client.login(username=self.user.username, password='password')
        data = {'tags': [self.tag_1.id, self.tag_2.id]}
        response = self.client.put(
            reverse('changeset:set-good', args=[self.changeset_2]),
            data
            )
        self.assertEqual(response.status_code, 200)
        self.changeset_2.refresh_from_db()
        self.assertFalse(self.changeset_2.harmful)
        self.assertTrue(self.changeset_2.checked)
        self.assertEqual(self.changeset_2.check_user, self.user)
        self.assertIsNotNone(self.changeset_2.check_date)
        self.assertEqual(self.changeset_2.tags.count(), 2)
        self.assertIn(
            self.tag_1,
            self.changeset_2.tags.all()
            )
        self.assertIn(
            self.tag_2,
            self.changeset_2.tags.all()
            )

    def test_set_good_changeset_with_invalid_tag_id(self):
        """Return a 400 error if a user try to add a invalid tag id to a changeset.
        """
        self.client.login(username=self.user.username, password='password')
        data = {'tags': [self.tag_1.id, 87765, 898986]}
        response = self.client.put(
            reverse('changeset:set-good', args=[self.changeset_2.pk]),
            data
            )

        self.assertEqual(response.status_code, 400)
        self.changeset_2.refresh_from_db()
        self.assertIsNone(self.changeset_2.harmful)
        self.assertFalse(self.changeset_2.checked)
        self.assertIsNone(self.changeset_2.check_user)
        self.assertIsNone(self.changeset_2.check_date)
        self.assertEqual(self.changeset_2.tags.count(), 0)

    def test_set_good_changeset_put_without_data(self):
        """Test marking a changeset as good without sending data (so the
        changeset will not receive tags).
        """
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:set-good', args=[self.changeset_2]),
            )
        self.assertEqual(response.status_code, 200)
        self.changeset_2.refresh_from_db()
        self.assertFalse(self.changeset_2.harmful)
        self.assertTrue(self.changeset_2.checked)
        self.assertEqual(self.changeset_2.check_user, self.user)
        self.assertIsNotNone(self.changeset_2.check_date)

    def test_404(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:set-good', args=[4988787832]),
            )
        self.assertEqual(response.status_code, 404)

        response = self.client.put(
            reverse('changeset:set-harmful', args=[4988787832]),
            )
        self.assertEqual(response.status_code, 404)

    def test_try_to_check_changeset_already_checked(self):
        """A PUT request to set_harmful or set_good urls of a checked changeset
        will not change anything on it.
        """
        changeset = HarmfulChangesetFactory(uid=333)
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:set-good', args=[changeset.pk]),
            )
        self.assertEqual(response.status_code, 403)
        changeset.refresh_from_db()
        self.assertNotEqual(changeset.check_user, self.user)

        data = {'tags': [self.tag_1.id, self.tag_2.id]}
        response = self.client.put(
            reverse('changeset:set-harmful', args=[changeset.pk]),
            data,
            )
        self.assertEqual(response.status_code, 403)
        changeset.refresh_from_db()
        self.assertNotEqual(changeset.check_user, self.user)


class TestUncheckChangesetView(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test_2',
            password='password',
            email='a@a.com'
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='123123',
            )
        self.suspect_changeset = SuspectChangesetFactory()
        self.good_changeset = GoodChangesetFactory(check_user=self.user)
        self.harmful_changeset = HarmfulChangesetFactory(check_user=self.user)
        self.harmful_changeset_2 = HarmfulChangesetFactory()
        self.tag = TagFactory(name='Vandalism')
        self.tag.changesets.set([
            self.good_changeset,
            self.harmful_changeset,
            self.harmful_changeset_2
            ])

    def test_unauthenticated_response(self):
        response = self.client.put(
            reverse('changeset:uncheck', args=[self.harmful_changeset.pk]),
            )
        self.assertEqual(response.status_code, 401)
        self.harmful_changeset.refresh_from_db()
        self.assertTrue(self.harmful_changeset.harmful)
        self.assertTrue(self.harmful_changeset.checked)
        self.assertEqual(self.harmful_changeset.check_user, self.user)
        self.assertIsNotNone(self.harmful_changeset.check_date)
        self.assertEqual(self.harmful_changeset.tags.count(), 1)
        self.assertIn(self.tag, self.harmful_changeset.tags.all())

    def test_uncheck_harmful_changeset(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:uncheck', args=[self.harmful_changeset.pk]),
            )
        self.assertEqual(response.status_code, 200)
        self.harmful_changeset.refresh_from_db()
        self.assertIsNone(self.harmful_changeset.harmful)
        self.assertFalse(self.harmful_changeset.checked)
        self.assertIsNone(self.harmful_changeset.check_user)
        self.assertIsNone(self.harmful_changeset.check_date)
        self.assertEqual(self.harmful_changeset.tags.count(), 0)
        self.assertNotIn(self.harmful_changeset, self.tag.changesets.all())

    def test_uncheck_good_changeset(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:uncheck', args=[self.good_changeset.pk]),
            )
        self.assertEqual(response.status_code, 200)
        self.good_changeset.refresh_from_db()
        self.assertIsNone(self.good_changeset.harmful)
        self.assertFalse(self.good_changeset.checked)
        self.assertIsNone(self.good_changeset.check_user)
        self.assertIsNone(self.good_changeset.check_date)
        self.assertEqual(self.good_changeset.tags.count(), 0)

    def test_user_uncheck_permission(self):
        """User can only uncheck changesets that he checked."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:uncheck', args=[self.harmful_changeset_2.pk]),
            )

        self.assertEqual(response.status_code, 403)
        self.harmful_changeset.refresh_from_db()
        self.assertTrue(self.harmful_changeset_2.harmful)
        self.assertTrue(self.harmful_changeset_2.checked)
        self.assertIsNotNone(self.harmful_changeset_2.check_user)
        self.assertIsNotNone(self.harmful_changeset_2.check_date)
        self.assertIn(self.tag, self.harmful_changeset_2.tags.all())

    def test_try_to_uncheck_unchecked_changeset(self):
        """It's not possible to uncheck an unchecked changeset!"""
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:uncheck', args=[self.suspect_changeset.pk]),
            )
        self.assertEqual(response.status_code, 403)


class TestAddTagToChangesetAPIView(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='user',
            email='c@a.com',
            password='password',
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='999',
            )
        self.changeset_user = User.objects.create_user(
            username='test',
            email='b@a.com',
            password='password',
            )
        UserSocialAuth.objects.create(
            user=self.changeset_user,
            provider='openstreetmap',
            uid='123123',
            )
        self.changeset = ChangesetFactory()
        self.checked_changeset = HarmfulChangesetFactory(check_user=self.user)
        self.tag = TagFactory(name='Not verified')

    def test_unauthenticated_can_not_add_tag(self):
        response = self.client.put(
            reverse('changeset:add-tag', args=[self.changeset.id, self.tag.id])
            )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.changeset.tags.count(), 0)

    def test_can_not_add_invalid_tag_id(self):
        """When the tag id does not exist, it will return a 404 response."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:add-tag', args=[self.changeset.id, 44534])
            )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.changeset.tags.count(), 0)

    def test_add_tag(self):
        """A user that is not the creator of the changeset can add tags to an
        unchecked changeset.
        """
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:add-tag', args=[self.changeset.id, self.tag.id])
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.changeset.tags.count(), 1)
        self.assertIn(self.tag, self.changeset.tags.all())

        # test add the same tag again
        response = self.client.put(
            reverse('changeset:add-tag', args=[self.changeset.id, self.tag.id])
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.changeset.tags.count(), 1)

    def test_add_tag_by_changeset_owner(self):
        """The user that created the changeset can not add tags to it."""
        self.client.login(username=self.changeset_user.username, password='password')
        response = self.client.put(
            reverse('changeset:add-tag', args=[self.changeset.id, self.tag.id])
            )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.changeset.tags.count(), 0)

    def test_add_tag_to_checked_changeset(self):
        """The user that checked the changeset can add tags to it."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:add-tag', args=[self.checked_changeset.id, self.tag.id])
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.checked_changeset.tags.count(), 1)
        self.assertIn(self.tag, self.checked_changeset.tags.all())

    def test_other_user_can_not_add_tag_to_checked_changeset(self):
        """A non staff user can not add tags to a changeset that other user have
        checked.
        """
        other_user = User.objects.create_user(
            username='other_user',
            email='b@a.com',
            password='password',
            )
        UserSocialAuth.objects.create(
            user=other_user,
            provider='openstreetmap',
            uid='28763',
            )
        self.client.login(username=other_user.username, password='password')
        response = self.client.put(
            reverse('changeset:add-tag', args=[self.checked_changeset.id, self.tag.id])
            )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.changeset.tags.count(), 0)

    def test_staff_user_add_tag_to_checked_changeset(self):
        """A staff user can add tags to a changeset."""
        staff_user = User.objects.create_user(
            username='admin',
            email='b@a.com',
            password='password',
            is_staff=True
            )
        UserSocialAuth.objects.create(
            user=staff_user,
            provider='openstreetmap',
            uid='28763',
            )
        self.client.login(username=staff_user.username, password='password')
        response = self.client.put(
            reverse('changeset:add-tag', args=[self.checked_changeset.id, self.tag.id])
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.checked_changeset.tags.count(), 1)
        self.assertIn(self.tag, self.checked_changeset.tags.all())


class TestRemoveTagToChangesetAPIView(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='user',
            email='c@a.com',
            password='password',
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='999',
            )
        self.changeset_user = User.objects.create_user(
            username='test',
            email='b@a.com',
            password='password',
            )
        UserSocialAuth.objects.create(
            user=self.changeset_user,
            provider='openstreetmap',
            uid='123123',
            )
        self.changeset = ChangesetFactory()
        self.checked_changeset = HarmfulChangesetFactory(check_user=self.user)
        self.tag = TagFactory(name='Not verified')
        self.changeset.tags.add(self.tag)

    def test_unauthenticated_can_not_remove_tag(self):
        response = self.client.put(
            reverse('changeset:remove-tag', args=[self.changeset.id, self.tag.id])
            )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.changeset.tags.count(), 1)

    def test_can_not_remove_invalid_tag_id(self):
        """When the tag id does not exist it will return a 404 response."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:remove-tag', args=[self.changeset.id, 44534])
            )
        self.assertEqual(response.status_code, 404)

    def test_remove_tag(self):
        """A user that is not the creator of the changeset can remote tags to an
        unchecked changeset.
        """
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:remove-tag', args=[self.changeset.id, self.tag.id])
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.changeset.tags.count(), 0)

    def test_remove_tag_by_changeset_owner(self):
        """The user that created the changeset can not remove its tags."""
        self.client.login(username=self.changeset_user.username, password='password')
        response = self.client.put(
            reverse('changeset:remove-tag', args=[self.changeset.id, self.tag.id])
            )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.changeset.tags.count(), 1)

    def test_remove_tag_of_checked_changeset(self):
        """The user that checked the changeset can remove its tags."""
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:remove-tag', args=[self.checked_changeset.id, self.tag.id])
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.checked_changeset.tags.count(), 0)

    def test_other_user_can_not_remove_tag_to_checked_changeset(self):
        """A non staff user can not remove tags of a changeset that other user
        have checked.
        """
        other_user = User.objects.create_user(
            username='other_user',
            email='b@a.com',
            password='password',
            )
        UserSocialAuth.objects.create(
            user=other_user,
            provider='openstreetmap',
            uid='28763',
            )
        self.client.login(username=other_user.username, password='password')
        response = self.client.put(
            reverse('changeset:remove-tag', args=[self.checked_changeset.id, self.tag.id])
            )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.changeset.tags.count(), 1)

    def test_staff_user_remove_tag_to_checked_changeset(self):
        """A staff user can remove tags to a changeset."""
        staff_user = User.objects.create_user(
            username='admin',
            email='b@a.com',
            password='password',
            is_staff=True
            )
        UserSocialAuth.objects.create(
            user=staff_user,
            provider='openstreetmap',
            uid='28763',
            )
        self.client.login(username=staff_user.username, password='password')
        response = self.client.put(
            reverse('changeset:remove-tag', args=[self.checked_changeset.id, self.tag.id])
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.checked_changeset.tags.count(), 0)


class TestThrottling(APITestCase):
    def setUp(self):
        self.changesets = SuspectChangesetFactory.create_batch(
            5, user='test2', uid='999999', editor='iD',
            )
        self.user = User.objects.create_user(
            username='test',
            password='password',
            email='a@a.com'
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='123123',
            )

    def test_set_harmful_throttling(self):
        """User can only check 3 changesets each minute."""
        self.client.login(username=self.user.username, password='password')
        for changeset in self.changesets:
            response = self.client.put(
                reverse('changeset:set-harmful', args=[changeset.pk]),
                )
        self.assertEqual(response.status_code, 429)
        self.assertEqual(Changeset.objects.filter(checked=True).count(), 3)

    def test_set_good_throttling(self):
        self.client.login(username=self.user.username, password='password')
        for changeset in self.changesets:
            response = self.client.put(
                reverse('changeset:set-good', args=[changeset.pk]),
                )
        self.assertEqual(response.status_code, 429)
        self.assertEqual(Changeset.objects.filter(checked=True).count(), 3)

    def test_mixed_throttling(self):
        """Test if both set_harmful and set_good views are throttled together."""
        self.client.login(username=self.user.username, password='password')
        three_changesets = self.changesets[:3]
        for changeset in three_changesets:
            response = self.client.put(
                reverse('changeset:set-good', args=[changeset.pk]),
                )
        self.assertEqual(response.status_code, 200)

        response = self.client.put(
            reverse('changeset:set-harmful', args=[self.changesets[3].pk]),
            )
        self.assertEqual(response.status_code, 429)
        self.assertEqual(Changeset.objects.filter(checked=True).count(), 3)

    def test_set_good_by_staff_user(self):
        """Staff users have not limit of checked changesets by minute."""
        user = User.objects.create_user(
            username='test_staff',
            password='password',
            email='a@a.com',
            is_staff=True
            )
        UserSocialAuth.objects.create(
            user=user,
            provider='openstreetmap',
            uid='8987',
            )
        self.client.login(username=user.username, password='password')
        for changeset in self.changesets:
            response = self.client.put(
                reverse('changeset:set-good', args=[changeset.pk]),
                )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Changeset.objects.filter(checked=True).count(), 5)

    def test_set_harmful_by_staff_user(self):
        """Staff users have not limit of checked changesets by minute."""
        user = User.objects.create_user(
            username='test_staff',
            password='password',
            email='a@a.com',
            is_staff=True
            )
        UserSocialAuth.objects.create(
            user=user,
            provider='openstreetmap',
            uid='8987',
            )
        self.client.login(username=user.username, password='password')
        for changeset in self.changesets:
            response = self.client.put(
                reverse('changeset:set-harmful', args=[changeset.pk]),
                )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Changeset.objects.filter(checked=True).count(), 5)
