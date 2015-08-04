from django.contrib.gis.db import models

from ..users.models import User


class SuspicionReasons(models.Model):

    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Changeset(models.Model):

    user = models.CharField(max_length=1000)
    editor = models.CharField(max_length=255)
    comment = models.CharField(max_length=255, blank=True)
    date = models.DateTimeField()
    reasons = models.ManyToManyField(SuspicionReasons, related_name='changesets')
    created = models.IntegerField()
    modified = models.IntegerField()
    deleted = models.IntegerField()
    bbox = models.PolygonField()
    harmful = models.NullBooleanField()
    checked = models.BooleanField(default=False)
    check_user = models.ForeignKey(User, blank=True, null=True)
    check_date = models.DateTimeField(null=True, blank=True)
    objects = models.GeoManager()

    def __str__(self):
        return '%s' % self.id