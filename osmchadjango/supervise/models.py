import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.gis.db import models
from django.db.models import JSONField
from django.http.request import HttpRequest
from django.utils import timezone

from osmchadjango.changeset.filters import ChangesetFilter

from ..users.models import User

IGNORED_FILTERS = ('date__gte', 'date__lte', 'last_days')


class AreaOfInterest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    filters = JSONField()
    geometry = models.GeometryField(blank=True, null=True)

    def __str__(self):
        return '{} by {}'.format(self.name, self.user.username)

    def changesets(self, request=None):
        """Return the changesets from the last AOI_WINDOW_DAYS days that match
        the filters, including the geometry of the AreaOfInterest. Date filters
        saved on the AoI are ignored, so that queries are always bounded to a
        recent time window. Fake a request object in order to execute the
        query with the user that created the AoI, not with the request user.
        """
        filters = {
            k: v for k, v in self.filters.items() if k not in IGNORED_FILTERS
            }
        request = HttpRequest
        request.user = self.user
        qs = ChangesetFilter(filters, request=request).qs.filter(
            date__gte=timezone.now() - timedelta(days=settings.AOI_WINDOW_DAYS)
            )
        if self.geometry is not None:
            return qs.filter(
                bbox__intersects=self.geometry
                )
        else:
            return qs

    class Meta:
        unique_together = ('user', 'name',)
        ordering = ['-date']
        verbose_name = 'Area of Interest'
        verbose_name_plural = 'Areas of Interest'


class BlacklistedUser(models.Model):
    username = models.CharField(max_length=1000)
    uid = models.CharField(max_length=255)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.uid

    def save(self, *args, **kwargs):
        self.full_clean()
        super(BlacklistedUser, self).save(*args, **kwargs)

    class Meta:
        unique_together = ('uid', 'added_by')
        ordering = ['-date']
