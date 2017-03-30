from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.client import encode_multipart

from social_django.models import UserSocialAuth
from rest_framework.test import APIClient

from ...users.models import User
from ..models import SuspicionReasons, HarmfulReason, Changeset, UserWhitelist
from .modelfactories import (
    ChangesetFactory, SuspectChangesetFactory, GoodChangesetFactory,
    HarmfulChangesetFactory, HarmfulReasonFactory, UserWhitelistFactory
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
        response = client.get(self.url, {'hide_whitelist': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 52)
        response = client.get(self.url, {'hide_whitelist': 'true', 'checked': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        # test with login. As all changesets in the DB are from a whitelisted
        # user, the features count will be zero
        self.client.login(username=user.username, password='password')
        response = self.client.get(self.url, {'hide_whitelist': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)


class TestChangesetCSVListView(TestCase):
    def setUp(self):
        SuspectChangesetFactory.create_batch(26)
        ChangesetFactory.create_batch(26)
        self.url = reverse('changeset:csv-list')

    def test_changeset_list_response(self):
        response = client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 52)
        response = client.get(self.url, {'is_suspect': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 26)


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
        self.changeset = HarmfulChangesetFactory(id=31982803)
        self.reason_1.changesets.add(self.changeset)
        self.reason_2.changesets.add(self.changeset)
        harmful_reason = HarmfulReason.objects.create(name='Vandalism')
        harmful_reason.changesets.add(self.changeset)

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
        self.assertIn(
            {'name': 'Vandalism', 'is_visible': True},
            response.data['properties']['harmful_reasons']
            )


class TestSuspicionReasonsAPIListView(TestCase):
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
        response = client.get(reverse('changeset:suspicion-reasons-list'))
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
        client.login(username=self.user.username, password='password')
        response = client.get(reverse('changeset:suspicion-reasons-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)


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
        self.changeset.refresh_from_db()
        self.assertIsNone(self.changeset.harmful)
        self.assertFalse(self.changeset.checked)
        self.assertIsNone(self.changeset.check_user)
        self.assertIsNone(self.changeset.check_date)

    def test_set_good_changeset_unlogged(self):
        response = client.put(
            reverse('changeset:set_good', args=[self.changeset])
            )
        self.assertEqual(response.status_code, 401)
        self.changeset.refresh_from_db()
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
        self.changeset.refresh_from_db()
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
        self.changeset.refresh_from_db()
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
        self.changeset_2.refresh_from_db()
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
        self.changeset_2.refresh_from_db()
        self.assertTrue(self.changeset_2.harmful)
        self.assertTrue(self.changeset_2.checked)
        self.assertEqual(self.changeset_2.check_user, self.user)
        self.assertIsNotNone(self.changeset_2.check_date)
        self.assertEqual(self.changeset_2.harmful_reasons.count(), 2)
        self.assertIn(
            self.harmful_reason_1,
            self.changeset_2.harmful_reasons.all()
            )
        self.assertIn(
            self.harmful_reason_2,
            self.changeset_2.harmful_reasons.all()
            )

    def test_set_harmful_changeset_put_without_data(self):
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
        self.assertEqual(self.changeset_2.harmful_reasons.count(), 0)

    def test_set_good_changeset_get(self):
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
            {'harmful_reasons': [self.harmful_reason_1.id, self.harmful_reason_2.id]}
            )
        response = self.client.put(
            reverse('changeset:set_harmful', args=[changeset.pk]),
            content,
            content_type='multipart/form-data; boundary=BoUnDaRyStRiNg'
            )
        self.assertEqual(response.status_code, 403)
        changeset.refresh_from_db()
        self.assertNotEqual(changeset.check_user, self.user)


class TestUncheckChangesetView(TestCase):
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
        self.reason = HarmfulReasonFactory(name='Vandalism')
        self.reason.changesets.add(self.harmful_changeset)
        self.reason.changesets.add(self.harmful_changeset_2)

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
        self.assertEqual(self.harmful_changeset.harmful_reasons.count(), 1)
        self.assertIn(self.reason, self.harmful_changeset.harmful_reasons.all())

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
        self.assertEqual(self.harmful_changeset.harmful_reasons.count(), 0)
        self.assertNotIn(self.harmful_changeset, self.reason.changesets.all())

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
        self.assertIn(self.reason, self.harmful_changeset_2.harmful_reasons.all())

    def test_try_to_uncheck_unchecked_changeset(self):
        """It's not possible to uncheck an unchecked changeset!"""
        self.client.login(username=self.user.username, password='password')
        response = self.client.put(
            reverse('changeset:uncheck', args=[self.suspect_changeset.pk]),
            )
        self.assertEqual(response.status_code, 403)


class TestWhitelistUserView(TestCase):
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


class TestUserWhitelistDestroyAPIView(TestCase):
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
