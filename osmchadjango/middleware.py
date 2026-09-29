import re

# Named regex groups, e.g. (?P<pk>\d+). Doesn't handle nested parentheses
# inside the group; none of our routes use them.
REGEX_GROUP = re.compile(r"\(\?P<(\w+)>[^()]*\)")
# Path converters, e.g. <int:pk> or <pk>
CONVERTER = re.compile(r"<(?:\w+:)?(\w+)>")


def format_route(route):
    """Convert a Django route pattern into a readable label, e.g.
    'api/v1/changesets/(?P<pk>\\d+)/$' -> '/api/v1/changesets/:pk/'.
    """
    route = REGEX_GROUP.sub(r":\1", route)
    route = CONVERTER.sub(r":\1", route)
    return "/" + route.replace("^", "").replace("$", "")


class RouteHeaderMiddleware:
    """Reports the matched route pattern in an X-Route response header, so
    that the reverse proxy's access logs can be aggregated by route without
    knowing this app's URL scheme.

    Requests that never reach the URL resolver (unmatched paths, redirects
    from CommonMiddleware, etc) get no header.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        match = request.resolver_match
        if match:
            response["X-Route"] = format_route(match.route)
        return response
