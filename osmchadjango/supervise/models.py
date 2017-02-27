from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField

from osmchadjango.changeset.filters import ChangesetFilter


class AreaOfInterest(models.Model):
    name = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey('users.User')
    filters = JSONField(blank=True, null=True)
    place = models.MultiPolygonField()

    def __str__(self):
        return '{} - {}'.format(self.id, self.name)

    def changesets(self):
        """Returns the changesets whose bbox intersects with the AreaOfInterest
        and weren't made by this user.
        """
        qs = ChangesetFilter(self.filters).qs
        return qs.filter(
            bbox__intersects=self.place
            ).exclude(user=self.user)
