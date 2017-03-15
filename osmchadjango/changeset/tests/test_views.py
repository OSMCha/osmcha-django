from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.client import encode_multipart

from social_django.models import UserSocialAuth
from rest_framework.test import APIClient

from ...users.models import User
from ..models import SuspicionReasons, HarmfulReason, Changeset
from .modelfactories import (
    ChangesetFactory, SuspectChangesetFactory, GoodChangesetFactory,
    HarmfulChangesetFactory, HarmfulReasonFactory
    )

client = APIClient()


class TestChangesetListView(TestCase):

    def setUp(self):
        SuspectChangesetFactory.create_batch(26)
        ChangesetFactory.create_batch(26)
        self.url = reverse('changeset:list')

    def test_changeset_list_response(self):
        response = client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['features']), 50)
        self.assertEqual(response.data['count'], 52)

    def test_pagination(self):
        response = client.get(self.url, {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['features']), 2)
        self.assertEqual(response.data['count'], 52)
        # test page_size parameter
        response = client.get(self.url, {'page_size': 60})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['features']), 52)

    def test_filters(self):
        response = client.get(self.url, {'in_bbox': '-72,43,-70,45'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 52)

        response = client.get(self.url, {'in_bbox': '-3.17,-91.98,-2.1,-90.5'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        response = client.get(self.url, {'is_suspect': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 26)

        response = client.get(self.url, {'is_suspect': 'false'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 26)


class TestChangesetFilteredViews(TestCase):
    def setUp(self):
        ChangesetFactory()
        SuspectChangesetFactory()
        HarmfulChangesetFactory()
        GoodChangesetFactory()

    def test_suspect_changesets_view(self):
        url = reverse('changeset:suspect-list')
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)

    def test_no_suspect_changesets_view(self):
        url = reverse('changeset:no-suspect-list')
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_harmful_changesets_view(self):
        url = reverse('changeset:harmful-list')
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_no_harmful_changesets_view(self):
        url = reverse('changeset:no-harmful-list')
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_checked_changesets_view(self):
        url = reverse('changeset:checked-list')
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)

    def test_unchecked_changesets_view(self):
        url = reverse('changeset:unchecked-list')
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)


class TestChangesetListViewOrdering(TestCase):

    def setUp(self):
        SuspectChangesetFactory.create_batch(2, delete=2)
        HarmfulChangesetFactory.create_batch(24, form_create=20, modify=2, delete=40)
        GoodChangesetFactory.create_batch(24, form_create=1000, modify=20)
        self.url = reverse('changeset:list')

    def test_ordering(self):
        # default ordering is by descending id
        response = client.get(self.url)
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.all()]
            )
        # ascending id
        response = client.get(self.url, {'order_by': 'id'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('id')]
            )
        # ascending date ordering
        response = client.get(self.url, {'order_by': 'date'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('date')]
            )
        # descending date ordering
        response = client.get(self.url, {'order_by': '-date'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('-date')]
            )
        # ascending check_date
        response = client.get(self.url, {'order_by': 'check_date'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('check_date')]
            )
        # descending check_date ordering
        response = client.get(self.url, {'order_by': '-check_date'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('-check_date')]
            )
        # ascending create ordering
        response = client.get(self.url, {'order_by': 'create'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('create')]
            )
        # descending create ordering
        response = client.get(self.url, {'order_by': '-create'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('-create')]
            )
        # ascending modify ordering
        response = client.get(self.url, {'order_by': 'modify'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('modify')]
            )
        # descending modify ordering
        response = client.get(self.url, {'order_by': '-modify'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('-modify')]
            )
        # ascending delete ordering
        response = client.get(self.url, {'order_by': 'delete'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('delete')]
            )
        # descending delete ordering
        response = client.get(self.url, {'order_by': '-delete'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.order_by('-delete')]
            )

    def test_invalid_ordering_field(self):
        # default ordering is by descending id
        response = client.get(self.url, {'order_by': 'user'})
        self.assertEqual(
            [i['id'] for i in response.data.get('features')],
            [i.id for i in Changeset.objects.all()]
            )


class TestChangesetDetailView(TestCase):

    def setUp(self):
        self.reason_1 = SuspicionReasons.objects.create(name='possible import')
        self.reason_2 = SuspicionReasons.objects.create(name='suspect word')
        self.changeset = ChangesetFactory(id=31982803)
        self.reason_1.changesets.add(self.changeset)
        self.reason_2.changesets.add(self.changeset)

    def test_changeset_detail_response(self):
        response = client.get(reverse('changeset:detail', args=[self.changeset.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('id'), 31982803)
        self.assertIn('properties', response.data.keys())
        self.assertIn('geometry', response.data.keys())
        self.assertIn(
            {'name': 'possible import', 'is_visible': True},
            response.data['properties']['reasons']
            )
        self.assertIn(
            {'name': 'suspect word', 'is_visible': True},
            response.data['properties']['reasons']
            )


class TestSuspicionReasonsAPIListView(TestCase):
    def setUp(self):
        self.reason_1 = SuspicionReasons.objects.create(
            name='possible import',
            description='A changeset that created too much map elements.'
            )
        self.reason_2 = SuspicionReasons.objects.create(name='suspect word')

    def test_view(self):
        response = client.get(reverse('changeset:suspicion-reasons-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        reason_dict = {
            'id': self.reason_1.id,
            'name': 'possible import',
            'description': self.reason_1.description,
            'is_visible': True,
            'for_changeset': True,
            'for_feature': True
            }
        self.assertIn(
            reason_dict,
            response.data
            )


class TestHarmfulReasonAPIListView(TestCase):
    def setUp(self):
        self.reason_1 = HarmfulReason.objects.create(
            name='Illegal import',
            description='A changeset that imported illegal data.'
            )
        self.reason_2 = HarmfulReason.objects.create(name='Vandalism')

    def test_view(self):
        response = client.get(reverse('changeset:harmful-reasons-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        reason_dict = {
            'id': self.reason_1.id,
            'name': 'Illegal import',
            'description': self.reason_1.description,
            'is_visible': True,
            'for_changeset': True,
            'for_feature': True
            }
        self.assertIn(
            reason_dict,
            response.data
            )


class TestCheckChangesetViews(TestCase):

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
        self.harmful_reason_1 = HarmfulReasonFactory(name='Illegal import')
        self.harmful_reason_2 = HarmfulReasonFactory(name='Vandalism')

    def test_set_harmful_changeset_unlogged(self):
        response = client.put(
            reverse('changeset:set_harmful', args=[self.changeset])
            )
        self.assertEqual(response.status_code, 401)
        self.assertIsNone(self.changeset.harmful)
        self.assertFalse(self.changeset.checked)
        self.assertIsNone(self.changeset.check_user)
        self.assertIsNone(self.changeset.check_date)

    def test_set_good_changeset_unlogged(self):
        response = client.put(
            reverse('changeset:set_good', args=[self.changeset])
            )
        self.assertEqual(response.status_code, 401)
        self.assertIsNone(self.changeset.harmful)
        self.assertFalse(self.changeset.checked)
        self.assertIsNone(self.changeset.check_user)
        self.assertIsNone(self.changeset.check_date)

    def test_set_harmful_changeset_not_allowed(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:set_harmful', args=[self.changeset])
            )

        self.assertEqual(response.status_code, 403)
        self.assertIsNone(self.changeset.harmful)
        self.assertFalse(self.changeset.checked)
        self.assertIsNone(self.changeset.check_user)
        self.assertIsNone(self.changeset.check_date)

    def test_set_good_changeset_not_allowed(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:set_good', args=[self.changeset])
            )

        self.assertEqual(response.status_code, 403)
        self.assertIsNone(self.changeset.harmful)
        self.assertFalse(self.changeset.checked)
        self.assertIsNone(self.changeset.check_user)
        self.assertIsNone(self.changeset.check_date)

    def test_set_harmful_changeset_get(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(
            reverse('changeset:set_harmful', args=[self.changeset_2]),
            )

        self.assertEqual(response.status_code, 405)
        self.assertIsNone(self.changeset_2.harmful)
        self.assertFalse(self.changeset_2.checked)
        self.assertIsNone(self.changeset_2.check_user)
        self.assertIsNone(self.changeset_2.check_date)

    def test_set_harmful_changeset_put(self):
        self.client.login(username=self.user.username, password='password')
        content = encode_multipart(
            'BoUnDaRyStRiNg',
            {'harmful_reasons': [self.harmful_reason_1.id, self.harmful_reason_2.id]}
            )
        response = self.client.put(
            reverse('changeset:set_harmful', args=[self.changeset_2.pk]),
            content,
            content_type='multipart/form-data; boundary=BoUnDaRyStRiNg'
            )

        self.assertEqual(response.status_code, 200)
        changeset_2 = Changeset.objects.get(id=31982804)
        self.assertTrue(changeset_2.harmful)
        self.assertTrue(changeset_2.checked)
        self.assertEqual(changeset_2.check_user, self.user)
        self.assertIsNotNone(changeset_2.check_date)
        self.assertEqual(changeset_2.harmful_reasons.count(), 2)
        self.assertIn(self.harmful_reason_1, changeset_2.harmful_reasons.all())
        self.assertIn(self.harmful_reason_2, changeset_2.harmful_reasons.all())

    def test_set_harmful_changeset_put_without_data(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:set_harmful', args=[self.changeset_2.pk])
            )

        self.assertEqual(response.status_code, 200)
        changeset_2 = Changeset.objects.get(id=31982804)
        self.assertTrue(changeset_2.harmful)
        self.assertTrue(changeset_2.checked)
        self.assertEqual(changeset_2.check_user, self.user)
        self.assertIsNotNone(changeset_2.check_date)
        self.assertEqual(changeset_2.harmful_reasons.count(), 0)

    def test_set_good_changeset_get(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.get(
            reverse('changeset:set_good', args=[self.changeset_2]),
            )

        self.assertEqual(response.status_code, 405)
        self.assertIsNone(self.changeset_2.harmful)
        self.assertFalse(self.changeset_2.checked)
        self.assertIsNone(self.changeset_2.check_user)
        self.assertIsNone(self.changeset_2.check_date)

    def test_set_good_changeset_put(self):
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:set_good', args=[self.changeset_2]),
            )
        self.assertEqual(response.status_code, 200)
        changeset_2 = Changeset.objects.get(id=31982804)
        self.assertFalse(changeset_2.harmful)
        self.assertTrue(changeset_2.checked)
        self.assertEqual(changeset_2.check_user, self.user)
        self.assertIsNotNone(changeset_2.check_date)

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
