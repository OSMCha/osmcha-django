from django.contrib.gis.db import models
from django.utils.translation import ugettext, ugettext_lazy as _

from ..users.models import User


class SuspicionReasons(models.Model):

    name = models.CharField(max_length=255, db_index=True)

    def __str__(self):
        return self.name

    @classmethod
    def merge(kls):
        '''
            Utility method to clean-up duplicate suspicious reasons
            For each distinct suspicious reason name, finds other reasons
            named the same, merges into the distinct reason, and then
            deletes the duplicated suspicious reason.
        '''
        distinct_reasons = kls.objects.all().distinct('name')
        for reason in distinct_reasons:
            same_reasons = kls.objects.filter(name=reason.name).exclude(pk=reason.pk)
            if same_reasons.count() > 0:
                for same_reason in same_reasons:
                    changesets = Changeset.objects.filter(reasons=same_reason)
                    for c in changesets:
                        c.reasons.remove(same_reason)
                        c.reasons.add(reason)
                    print "deleting %s" % same_reason.name
                    same_reason.delete()


class SuspicionScore(models.Model):
    changeset = models.ForeignKey("Changeset")
    score = models.IntegerField()
    reason = models.CharField(max_length=255)

    class Meta:
        unique_together = ('changeset', 'score', 'reason',)


class UserSuspicionScore(models.Model):
    user = models.ForeignKey("UserDetail")
    score = models.IntegerField()
    reason = models.CharField(max_length=255)

    class Meta:
        unique_together = ('user', 'score', 'reason',)


class UserWhitelist(models.Model):
    user = models.ForeignKey(User)
    whitelist_user = models.CharField(max_length=1000)

    def __str__(self):
        return '%s' % self.whitelist_user

    class Meta:
        unique_together = ('user', 'whitelist_user',)


class UserDetail(models.Model):
    contributor_uid = models.IntegerField(blank=True, null=True, db_index=True)
    contributor_name = models.CharField(max_length=1000, unique=True)
    contributor_blocks = models.IntegerField()
    contributor_since = models.DateTimeField(null=True, blank=True)
    contributor_traces = models.IntegerField(null=True, blank=True)
    contributor_img = models.CharField(max_length=512, blank=True, null=True)

    nodes_c = models.IntegerField(null=True, blank=True)
    nodes_m = models.IntegerField(null=True, blank=True)
    nodes_d = models.IntegerField(null=True, blank=True)
    nodes_rank = models.IntegerField(null=True, blank=True)

    ways_c = models.IntegerField(null=True, blank=True)
    ways_m = models.IntegerField(null=True, blank=True)
    ways_d = models.IntegerField(null=True, blank=True)
    ways_rank = models.IntegerField(null=True, blank=True)

    relations_c = models.IntegerField(null=True, blank=True)
    relations_m = models.IntegerField(null=True, blank=True)
    relations_d = models.IntegerField(null=True, blank=True)
    relations_rank = models.IntegerField(null=True, blank=True)

    notes_opened = models.IntegerField(null=True, blank=True)
    notes_commented = models.IntegerField(null=True, blank=True)
    notes_closed = models.IntegerField(null=True, blank=True)

    changesets_no = models.IntegerField(null=True, blank=True, help_text='Number of changesets', db_index=True)
    changesets_changes = models.IntegerField(null=True, blank=True, db_index=True)
    changesets_f_tstamp = models.DateTimeField(null=True, blank=True)
    changesets_l_tstamp = models.DateTimeField(null=True, blank=True)
    changesets_mapping_days = models.CharField(max_length=128, blank=True, null=True)

    score = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return self.contributor_name


class Changeset(models.Model):

    user = models.CharField(max_length=1000, db_index=True)
    uid = models.CharField(_('User ID'), max_length=255)
    user_detail = models.ForeignKey(UserDetail, blank=True, null=True)
    editor = models.CharField(max_length=255, blank=True, null=True)
    powerfull_editor = models.BooleanField(_('Powerfull Editor'), default=False)
    comment = models.CharField(max_length=1000, blank=True, null=True)
    source = models.CharField(max_length=1000, blank=True, null=True)
    imagery_used = models.CharField(max_length=1000, blank=True, null=True)
    date = models.DateTimeField(null=True)
    reasons = models.ManyToManyField(
        SuspicionReasons, related_name='changesets')
    create = models.IntegerField(db_index=True, null=True)
    modify = models.IntegerField(db_index=True, null=True)
    delete = models.IntegerField(db_index=True, null=True)
    bbox = models.PolygonField(null=True)
    is_suspect = models.BooleanField(db_index=True)
    harmful = models.NullBooleanField()
    checked = models.BooleanField(default=False)
    check_user = models.ForeignKey(User, null=True, blank=True)
    check_date = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(null=True, blank=True)
    objects = models.GeoManager()

    def __str__(self):
        return '%s' % self.id

    def osm_link(self):
        """Return the link to the changeset page on OSM website."""
        return 'http://www.openstreetmap.org/changeset/%s' % self.id

    def achavi_link(self):
        """Return the link to the changeset page on ACHAVI."""
        return 'https://overpass-api.de/achavi/?changeset=%s' % self.id

    def josm_link(self):
        """Return link to open changeset in JOSM."""
        josm_base = "http://127.0.0.1:8111/import?url="
        changeset_url = "http://www.openstreetmap.org/api/0.6/changeset/%s/download" % self.id
        return "%s%s" % (josm_base, changeset_url,)

    def save_user_details(self, ch):
        user_details = ch.user_details
        user_details['score'] = ch.user_score
        # If UserDetail with contributor_name exists, update it with latest data.
        # Else, create a new UserDetail object
        print user_details
        user_detail, created = UserDetail.objects.update_or_create(
            contributor_name=user_details['contributor_name'],
            defaults=user_details
        )
        self.user_detail = user_detail
        self.save()

        UserSuspicionScore.objects.filter(user=user_detail).delete()
        for detail in ch.user_score_details:
            uss = UserSuspicionScore(user=user_detail)
            uss.score = detail['score']
            uss.reason = detail['reason']
            uss.save()
            
        return user_detail


class SuspiciousFeature(models.Model):
    changeset = models.ForeignKey('Changeset')
    reasons = models.ManyToManyField('SuspicionReasons')
    score = models.IntegerField(blank=True, null=True)
    osm_id = models.IntegerField()
    geometry = models.GeometryField()
    geojson = models.TextField()

    @property
    def osm_link(self):
        return "https://openstreetmap.org/%s/%d" % (self.get_type(), self.osm_id)

    def get_type(self):
        '''
        Returns either 'node' or 'way' based on geometry type
        '''
        if self.geometry.geom_type == 'Point':
            return 'node'
        else:
            return 'way'

    def __unicode__(self):
        return "%d" % self.osm_id



class Import(models.Model):
    """Class to register the import of Changesets."""
    start = models.IntegerField()
    end = models.IntegerField()
    date = models.DateTimeField(_('Date of the import'), auto_now_add=True)

    def __str__(self):
        return '%s %i - %i' % (_('Import'), self.start, self.end)

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Import, self).save(*args, **kwargs)
