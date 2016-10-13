from django.contrib.gis.db import models
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.postgres.fields import JSONField

from ..users.models import User
import json

class Feature(models.Model):

    user_detail = models.ForeignKey('changeset.UserDetail', blank=True, null=True)
    
    changeset = models.ForeignKey('changeset.Changeset')
    geometry = models.GeometryField()
    geojson = JSONField()
    reasons = models.ManyToManyField(
        'changeset.SuspicionReasons', related_name='features')
    harmful = models.NullBooleanField()
    checked = models.BooleanField(default=False)
    check_user = models.ForeignKey(User, null=True, blank=True)
    check_date = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(null=True, blank=True)
 
    def __str__(self):
        return '%s' % self.id

    @property
    def geojson_obj(self):
        return json.loads((self.geojson).replace('osm:', 'osm_'))