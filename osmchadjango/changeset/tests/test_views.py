from django.test import TestCase, Client
from django.core.urlresolvers import reverse

client = Client()


class TestChangesetListView(TestCase):

    def setUp(self):
        pass

    def test_changeset_home_response(self):
        response = client.get(reverse('changeset:home'))
        self.assertEqual(response.status_code, 200)
