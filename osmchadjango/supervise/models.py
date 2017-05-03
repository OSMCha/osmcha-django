import uuid

from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField

from osmchadjango.changeset.filters import ChangesetFilter


class AreaOfInterest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey('users.User')
    filters = JSONField(blank=True, null=True)
    geometry = models.MultiPolygonField(blank=True, null=True)
    objects = models.GeoManager()

    def __str__(self):
        return '{} by {}'.format(self.name, self.user.username)

    def changesets(self):
        """Returns the changesets whose bbox intersects with the AreaOfInterest
        and that matches the filters.
        """
        return ChangesetFilter(self.filters).qs

    class Meta:
        unique_together = ('user', 'name',)
