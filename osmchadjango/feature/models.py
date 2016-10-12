from django.contrib.gis.db import models
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.postgres.fields import JSONField

from ..users.models import User
import json

# class SuspiciousFeature(models.Model):
#     changeset = models.ForeignKey('Changeset')
#     reasons = models.ManyToManyField('SuspicionReasons')
#     score = models.IntegerField(blank=True, null=True)
#     osm_id = models.IntegerField()
#     geometry = models.GeometryField()
#     geojson = models.TextField()

#     #timestamp when feature was added to db
#     timestamp = models.DateTimeField(blank=True, null=True, auto_now_add=True)

#     @property
#     def osm_link(self):
#         return "https://openstreetmap.org/%s/%d" % (self.get_type(), self.osm_id)

#     def get_type(self):
#         '''
#         Returns either 'node' or 'way' based on geometry type
#         '''
#         if self.geometry.geom_type == 'Point':
#             return 'node'
#         else:
#             return 'way'

#     def __unicode__(self):
#         return "%d" % self.osm_id


class Feature(models.Model):

    # user = models.CharField(max_length=1000, db_index=True)
    # uid = models.CharField(_('User ID'), max_length=255)
    user_detail = models.ForeignKey('changeset.UserDetail', blank=True, null=True)
    
    changeset = models.ForeignKey('changeset.Changeset')
    geometry = models.GeometryField()
    geojson = JSONField()
    # editor = models.CharField(max_length=255, blank=True, null=True)
    # powerfull_editor = models.BooleanField(_('Powerfull Editor'), default=False)
    # comment = models.CharField(max_length=1000, blank=True, null=True)
    # source = models.CharField(max_length=1000, blank=True, null=True)
    # imagery_used = models.CharField(max_length=1000, blank=True, null=True)
    # date = models.DateTimeField(null=True)
    reasons = models.ManyToManyField(
        'changeset.SuspicionReasons', related_name='features')
    # create = models.IntegerField(db_index=True, null=True)
    # modify = models.IntegerField(db_index=True, null=True)
    # delete = models.IntegerField(db_index=True, null=True)
    # bbox = models.PolygonField(null=True)
    # is_suspect = models.BooleanField(db_index=True)
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
    # objects = models.GeoManager()

    # def __str__(self):
    #     return '%s' % self.id

    # def osm_link(self):
    #     """Return the link to the changeset page on OSM website."""
    #     return 'http://www.openstreetmap.org/changeset/%s' % self.id

    # def achavi_link(self):
    #     """Return the link to the changeset page on ACHAVI."""
    #     return 'https://osmlab.github.io/changeset-map/#%s' % self.id

    # def josm_link(self):
    #     """Return link to open changeset in JOSM."""
    #     josm_base = "http://127.0.0.1:8111/import?url="
    #     changeset_url = "http://www.openstreetmap.org/api/0.6/changeset/%s/download" % self.id
    #     return "%s%s" % (josm_base, changeset_url,)

    # def save_user_details(self, ch):
    #     user_details = ch.user_details
    #     user_details['score'] = ch.user_score
    #     # If UserDetail with contributor_name exists, update it with latest data.
    #     # Else, create a new UserDetail object
    #     print user_details
    #     user_detail, created = UserDetail.objects.update_or_create(
    #         contributor_name=user_details['contributor_name'],
    #         defaults=user_details
    #     )
    #     self.user_detail = user_detail
    #     self.save()

    #     UserSuspicionScore.objects.filter(user=user_detail).delete()
    #     for detail in ch.user_score_details:
    #         uss = UserSuspicionScore(user=user_detail)
    #         uss.score = detail['score']
    #         uss.reason = detail['reason']
    #         uss.save()
            
    #     return user_detail

