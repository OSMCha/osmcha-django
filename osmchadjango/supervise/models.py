import uuid
from datetime import timedelta

from django.contrib.gis.db import models
from django.db.models import JSONField
from django.http.request import HttpRequest
from django.utils import timezone

from osmchadjango.changeset.filters import ChangesetFilter

from ..users.models import User


class AreaOfInterest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    filters = JSONField()
    geometry = models.GeometryField(blank=True, null=True)

    def __str__(self):
        return '{} by {}'.format(self.name, self.user.username)

    def changesets(self, request=None, window_days=None):
        """Return the changesets that match the filters, including the geometry
        of the AreaOfInterest. If window_days is given, results are further
        limited to changesets from the last window_days days (this caps any
        saved date__gte filter, but doesn't override it). Fake a request object
        in order to execute the query with the user that created the AoI, not
        with the request user.
        """
        filters = dict(self.filters)

        # Pass the parsed geometry rather than the saved filter value, because
        # ChangesetFilter silently skips a 'geometry' value it can't parse (such
        # as a GeoJSON object rather than a string). This also covers 'in_bbox',
        # which ChangesetFilter doesn't apply itself.
        if self.geometry is not None:
            filters['geometry'] = self.geometry

        request = HttpRequest
        request.user = self.user
        qs = ChangesetFilter(filters, request=request).qs
        if window_days is not None:
            qs = qs.filter(date__gte=timezone.now() - timedelta(days=window_days))
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
