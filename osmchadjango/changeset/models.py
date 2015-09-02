from django.contrib.gis.db import models

from ..users.models import User


class SuspicionReasons(models.Model):

    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Changeset(models.Model):

    user = models.CharField(max_length=1000)
    editor = models.CharField(max_length=255)
    powerfull_editor = models.BooleanField(default=False)
    comment = models.CharField(max_length=1000, blank=True)
    source = models.CharField(max_length=1000, blank=True)
    imagery_used = models.CharField(max_length=1000, blank=True)
    date = models.DateTimeField()
    reasons = models.ManyToManyField(SuspicionReasons, related_name='changesets')
    create = models.IntegerField()
    modify = models.IntegerField()
    delete = models.IntegerField()
    bbox = models.PolygonField()
    is_suspect = models.BooleanField()
    checked = models.BooleanField(default=False)
    check_user = models.ForeignKey(User, blank=True, null=True)
    check_date = models.DateTimeField(null=True, blank=True)
    objects = models.GeoManager()

    def __str__(self):
        return '%s' % self.id

    def osm_link(self):
        return 'http://www.openstreetmap.org/changeset/%s' % self.id

    def achavi_link(self):
        return 'https://overpass-api.de/achavi/?changeset=%s' % self.id
