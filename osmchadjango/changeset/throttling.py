from rest_framework.throttling import UserRateThrottle
from rest_framework.compat import is_authenticated


class NonStaffUserThrottle(UserRateThrottle):
    scope = 'non_staff_user'

    def get_cache_key(self, request, view):
        if is_authenticated(request.user):
            if request.user.is_staff:
                return None
            else:
                ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
            }
