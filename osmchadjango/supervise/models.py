import uuid

from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField

from osmchadjango.changeset.filters import ChangesetFilter
from osmchadjango.feature.filters import FeatureFilter


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
        """Returns the changesets that matches the filters and geometry of
        the AreaOfInterest.
        """
        return ChangesetFilter(self.filters).qs

    def features(self):
        """Returns the features that matches the filters and geometry of
        the AreaOfInterest.
        """
        return FeatureFilter(self.filters).qs

    class Meta:
        unique_together = ('user', 'name',)
        verbose_name = 'Area of Interest'
        verbose_name_plural = 'Areas of Interest'
