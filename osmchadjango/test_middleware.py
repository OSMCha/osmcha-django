from django.test import SimpleTestCase, TestCase

from .middleware import format_route


class TestFormatRoute(SimpleTestCase):
    def test_regex_route(self):
        self.assertEqual(
            format_route(r"api/v1/aoi/(?P<pk>[0-9a-f-]+)/changesets/$"),
            "/api/v1/aoi/:pk/changesets/",
        )

    def test_path_route(self):
        self.assertEqual(
            format_route(
                "api/v1/changesets/<int:pk>/review-feature/<str:type>-<int:id>/"
            ),
            "/api/v1/changesets/:pk/review-feature/:type-:id/",
        )


class TestRouteHeader(TestCase):
    def test_matched_route(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response["X-Route"], "/api/v1/health")

    def test_unmatched_route(self):
        response = self.client.get("/nonexistent")
        self.assertNotIn("X-Route", response)
