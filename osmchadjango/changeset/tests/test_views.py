import json

from django.contrib.gis.geos import Polygon
from django.core.urlresolvers import reverse
from django.test.client import encode_multipart

from social_django.models import UserSocialAuth
from rest_framework.test import APITestCase

from ...users.models import User
from ...feature.tests.modelfactories import FeatureFactory
from ..models import SuspicionReasons, Tag, Changeset, UserWhitelist
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


class TestSuspicionReasonsAPIListView(APITestCase):
    def setUp(self):
        self.reason_1 = SuspicionReasons.objects.create(
            name='possible import',
            description='A changeset that created too much map elements.'
            )
        self.reason_2 = SuspicionReasons.objects.create(
            name='suspect word',
            is_visible=False
            )
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

    def test_view(self):
        response = self.client.get(reverse('changeset:suspicion-reasons-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        reason_dict = {
            'id': self.reason_1.id,
            'name': 'possible import',
            'description': self.reason_1.description,
            'is_visible': True,
            'for_changeset': True,
            'for_feature': True
            }
        self.assertIn(reason_dict, response.data)

    def test_admin_user_request(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(reverse('changeset:suspicion-reasons-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)


class TestTagListAPIView(APITestCase):
    def setUp(self):
        self.tag_1 = Tag.objects.create(
            name='Illegal import',
            description='A changeset that imported illegal data.'
            )
        self.tag_2 = Tag.objects.create(
            name='Vandalism in my city',
            is_visible=False
            )
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

    def test_view(self):
        response = self.client.get(reverse('changeset:tags-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        tag_dict = {
            'id': self.tag_1.id,
            'name': 'Illegal import',
            'description': self.tag_1.description,
            'is_visible': True,
            'for_changeset': True,
            'for_feature': True
            }
        self.assertIn(
            tag_dict,
            response.data
            )

    def test_admin_user_request(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(reverse('changeset:tags-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)


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
            reverse('changeset:set_harmful', args=[self.changeset])
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
            reverse('changeset:set_good', args=[self.changeset])
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
            reverse('changeset:set_harmful', args=[self.changeset])
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
            reverse('changeset:set_good', args=[self.changeset])
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
            reverse('changeset:set_harmful', args=[self.changeset_2]),
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
        content = encode_multipart(
            'BoUnDaRyStRiNg',
            {'tags': [self.tag_1.id, self.tag_2.id]}
            )
        response = self.client.put(
            reverse('changeset:set_harmful', args=[self.changeset_2.pk]),
            content,
            content_type='multipart/form-data; boundary=BoUnDaRyStRiNg'
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

    def test_set_harmful_changeset_put_without_data(self):
        """Test marking a changeset as harmful without sending data (so the
        changeset will not receive tags).
        """
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:set_harmful', args=[self.changeset_2.pk])
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
            reverse('changeset:set_good', args=[self.changeset_2]),
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
        content = encode_multipart(
            'BoUnDaRyStRiNg',
            {'tags': [self.tag_1.id, self.tag_2.id]}
            )
        response = self.client.put(
            reverse('changeset:set_good', args=[self.changeset_2]),
            content,
            content_type='multipart/form-data; boundary=BoUnDaRyStRiNg'
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

    def test_set_good_changeset_put_without_data(self):
        """Test marking a changeset as good without sending data (so the
        changeset will not receive tags).
        """
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:set_good', args=[self.changeset_2]),
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
            reverse('changeset:set_good', args=[4988787832]),
            )
        self.assertEqual(response.status_code, 404)

        response = self.client.put(
            reverse('changeset:set_harmful', args=[4988787832]),
            )
        self.assertEqual(response.status_code, 404)

    def test_try_to_check_changeset_already_checked(self):
        """A PUT request to set_harmful or set_good urls of a checked changeset
        will not change anything on it.
        """
        changeset = HarmfulChangesetFactory(uid=333)
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:set_good', args=[changeset.pk]),
            )
        self.assertEqual(response.status_code, 403)
        changeset.refresh_from_db()
        self.assertNotEqual(changeset.check_user, self.user)

        content = encode_multipart(
            'BoUnDaRyStRiNg',
            {'tags': [self.tag_1.id, self.tag_2.id]}
            )
        response = self.client.put(
            reverse('changeset:set_harmful', args=[changeset.pk]),
            content,
            content_type='multipart/form-data; boundary=BoUnDaRyStRiNg'
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
                reverse('changeset:set_harmful', args=[changeset.pk]),
                )
        self.assertEqual(response.status_code, 429)
        self.assertEqual(Changeset.objects.filter(checked=True).count(), 3)

    def test_set_good_throttling(self):
        self.client.login(username=self.user.username, password='password')
        for changeset in self.changesets:
            response = self.client.put(
                reverse('changeset:set_good', args=[changeset.pk]),
                )
        self.assertEqual(response.status_code, 429)
        self.assertEqual(Changeset.objects.filter(checked=True).count(), 3)

    def test_mixed_throttling(self):
        """Test if both set_harmful and set_good views are throttled together."""
        self.client.login(username=self.user.username, password='password')
        three_changesets = self.changesets[:3]
        for changeset in three_changesets:
            response = self.client.put(
                reverse('changeset:set_good', args=[changeset.pk]),
                )
        self.assertEqual(response.status_code, 200)

        response = self.client.put(
            reverse('changeset:set_harmful', args=[self.changesets[3].pk]),
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
                reverse('changeset:set_good', args=[changeset.pk]),
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
                reverse('changeset:set_harmful', args=[changeset.pk]),
                )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Changeset.objects.filter(checked=True).count(), 5)


class TestWhitelistUserView(APITestCase):
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
        self.user_2 = User.objects.create_user(
            username='test_user',
            password='password',
            email='b@a.com'
            )
        UserSocialAuth.objects.create(
            user=self.user_2,
            provider='openstreetmap',
            uid='444444',
            )
        self.url = reverse('changeset:whitelist-user')

    def test_list_whitelist_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_create_whitelist_unauthenticated(self):
        response = self.client.post(self.url, {'whitelist_user': 'good_user'})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(UserWhitelist.objects.count(), 0)

    def test_create_and_list_whitelist(self):
        # test whitelisting a user and getting the list of whitelisted users
        self.client.login(username=self.user.username, password='password')
        response = self.client.post(self.url, {'whitelist_user': 'good_user'})
        self.assertEqual(response.status_code, 201)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.client.logout()
        # the same with another user
        self.client.login(username=self.user_2.username, password='password')
        response = self.client.post(self.url, {'whitelist_user': 'the_user'})
        self.assertEqual(response.status_code, 201)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        self.assertEqual(UserWhitelist.objects.count(), 2)
        self.assertEqual(UserWhitelist.objects.filter(user=self.user).count(), 1)
        self.assertEqual(UserWhitelist.objects.filter(user=self.user_2).count(), 1)
        self.assertEqual(
            UserWhitelist.objects.filter(whitelist_user='good_user').count(), 1
            )
        self.assertEqual(
            UserWhitelist.objects.filter(whitelist_user='the_user').count(), 1
            )


class TestUserWhitelistDestroyAPIView(APITestCase):
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
        UserWhitelist.objects.create(user=self.user, whitelist_user='good_user')
        self.user_2 = User.objects.create_user(
            username='test_user',
            password='password',
            email='b@a.com'
            )
        UserSocialAuth.objects.create(
            user=self.user_2,
            provider='openstreetmap',
            uid='444444',
            )
        UserWhitelist.objects.create(user=self.user_2, whitelist_user='the_user')

    def test_delete_whitelist_unauthenticated(self):
        response = self.client.delete(
            reverse('changeset:delete-whitelist-user', args=['good_user'])
            )
        self.assertEqual(response.status_code, 401)
        response = self.client.delete(
            reverse('changeset:delete-whitelist-user', args=['the_user'])
            )
        self.assertEqual(response.status_code, 401)

    def test_delete_userwhitelist(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.delete(
            reverse('changeset:delete-whitelist-user', args=['good_user'])
            )
        self.assertEqual(response.status_code, 204)
        # test delete a whitelist of another user
        response = self.client.delete(
            reverse('changeset:delete-whitelist-user', args=['the_user'])
            )
        self.assertEqual(response.status_code, 404)
        self.client.logout()

        self.client.login(username=self.user_2.username, password='password')
        response = self.client.delete(
            reverse('changeset:delete-whitelist-user', args=['the_user'])
            )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(UserWhitelist.objects.count(), 0)


class TestStatsView(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test_user',
            email='b@a.com',
            password='password',
            is_staff=True
            )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='openstreetmap',
            uid='123123',
            )
        self.changeset = ChangesetFactory()
        self.suspect_changeset = SuspectChangesetFactory()
        self.harmful_changeset = HarmfulChangesetFactory(user='another_user')
        self.harmful_changeset_2 = HarmfulChangesetFactory()
        self.good_changeset = GoodChangesetFactory()
        self.reason_1 = SuspicionReasons.objects.create(name='possible import')
        self.reason_2 = SuspicionReasons.objects.create(name='suspect_word')
        self.reason_3 = SuspicionReasons.objects.create(
            name='vandalism in my city', is_visible=False)
        self.reason_1.changesets.set(
            [self.suspect_changeset, self.harmful_changeset]
            )
        self.reason_2.changesets.set(
            [self.harmful_changeset_2, self.good_changeset]
            )
        self.reason_3.changesets.set(
            [self.harmful_changeset_2, self.good_changeset]
            )
        self.tag_1 = Tag.objects.create(name='Vandalism')
        self.tag_2 = Tag.objects.create(name='Minor errors')
        self.tag_3 = Tag.objects.create(name='Big buildings', is_visible=False)
        self.tag_1.changesets.set(
            [self.harmful_changeset, self.harmful_changeset_2]
            )
        self.tag_2.changesets.add(self.good_changeset)
        self.tag_3.changesets.set(
            [self.harmful_changeset, self.harmful_changeset_2, self.good_changeset]
            )
        self.url = reverse('changeset:stats')

    def test_stats_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('checked_changesets'), 3)
        self.assertEqual(response.data.get('harmful_changesets'), 2)
        self.assertEqual(response.data.get('users_with_harmful_changesets'), 2)
        self.assertEqual(len(response.data.get('reasons')), 2)
        self.assertEqual(len(response.data.get('tags')), 2)
        self.assertIn(
            {'name': 'possible import', 'checked_changesets': 1, 'harmful_changesets': 1},
            response.data.get('reasons')
            )
        self.assertIn(
            {'name': 'suspect_word', 'checked_changesets': 2, 'harmful_changesets': 1},
            response.data.get('reasons')
            )
        self.assertIn(
            {'name': 'Vandalism', 'checked_changesets': 2, 'harmful_changesets': 2},
            response.data.get('tags')
            )
        self.assertIn(
            {'name': 'Minor errors', 'checked_changesets': 1, 'harmful_changesets': 0},
            response.data.get('tags')
            )

    def test_stats_view_with_filters(self):
        response = self.client.get(self.url, {'harmful': False})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('checked_changesets'), 1)
        self.assertEqual(response.data.get('harmful_changesets'), 0)
        self.assertEqual(response.data.get('users_with_harmful_changesets'), 0)
        self.assertEqual(len(response.data.get('reasons')), 2)
        self.assertEqual(len(response.data.get('tags')), 2)
        self.assertIn(
            {'name': 'possible import', 'checked_changesets': 0, 'harmful_changesets': 0},
            response.data.get('reasons')
            )
        self.assertIn(
            {'name': 'suspect_word', 'checked_changesets': 1, 'harmful_changesets': 0},
            response.data.get('reasons')
            )
        self.assertIn(
            {'name': 'Vandalism', 'checked_changesets': 0, 'harmful_changesets': 0},
            response.data.get('tags')
            )
        self.assertIn(
            {'name': 'Minor errors', 'checked_changesets': 1, 'harmful_changesets': 0},
            response.data.get('tags')
            )

    def test_stats_view_with_staff_user(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get('reasons')), 3)
        self.assertEqual(len(response.data.get('tags')), 3)
        self.assertIn(
            {'name': 'vandalism in my city', 'checked_changesets': 2, 'harmful_changesets': 1},
            response.data.get('reasons')
            )
        self.assertIn(
            {'name': 'Big buildings', 'checked_changesets': 3, 'harmful_changesets': 2},
            response.data.get('tags')
            )


class TestUserStatsViews(APITestCase):
    def setUp(self):
        GoodChangesetFactory(user='user_one', uid='4321')
        HarmfulChangesetFactory(user='user_one', uid='4321')
        SuspectChangesetFactory(user='user_one', uid='4321')

    def test_user_one_stats(self):
        response = self.client.get(reverse('changeset:user-stats', args=['4321']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('changesets_in_osmcha'), 3)
        self.assertEqual(response.data.get('checked_changesets'), 2)
        self.assertEqual(response.data.get('harmful_changesets'), 1)

    def test_user_without_changesets(self):
        response = self.client.get(reverse('changeset:user-stats', args=['1611']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('changesets_in_osmcha'), 0)
        self.assertEqual(response.data.get('checked_changesets'), 0)
        self.assertEqual(response.data.get('harmful_changesets'), 0)
