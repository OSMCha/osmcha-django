from django.conf import settings
from django.contrib.gis.db import models
from django.utils.translation import ugettext, ugettext_lazy as _

from ..users.models import User


class SuspicionReasons(models.Model):
    name = models.CharField(max_length=255, db_index=True, unique=True)
    description = models.CharField(max_length=1000, blank=True)
    is_visible = models.BooleanField(default=True)
    for_changeset = models.BooleanField(default=True)
    for_feature = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.full_clean()
        super(SuspicionReasons, self).save(*args, **kwargs)

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
                    print("deleting %s" % same_reason.name)
                    same_reason.delete()

    class Meta:
        verbose_name = 'Suspicion reason'
        verbose_name_plural = 'Suspicion reasons'


class HarmfulReason(models.Model):
    name = models.CharField(max_length=255, db_index=True, unique=True)
    description = models.CharField(max_length=1000, blank=True)
    is_visible = models.BooleanField(default=True)
    for_changeset = models.BooleanField(default=True)
    for_feature = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.full_clean()
        super(HarmfulReason, self).save(*args, **kwargs)


class UserWhitelist(models.Model):
    user = models.ForeignKey(User)
    whitelist_user = models.CharField(max_length=1000, db_index=True)

    def __str__(self):
        return '{} whitelisted by {}'.format(self.whitelist_user, self.user)

    class Meta:
        unique_together = ('user', 'whitelist_user',)


class Changeset(models.Model):

    user = models.CharField(max_length=1000, db_index=True)
    uid = models.CharField(_('User ID'), max_length=255)
    editor = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    powerfull_editor = models.BooleanField(_('Powerfull Editor'), default=False)
    comment = models.CharField(max_length=1000, blank=True, null=True, db_index=True)
    source = models.CharField(max_length=1000, blank=True, null=True)
    imagery_used = models.CharField(max_length=1000, blank=True, null=True)
    date = models.DateTimeField(null=True, db_index=True)
    reasons = models.ManyToManyField(SuspicionReasons, related_name='changesets')
    create = models.IntegerField(db_index=True, null=True)
    modify = models.IntegerField(db_index=True, null=True)
    delete = models.IntegerField(db_index=True, null=True)
    bbox = models.PolygonField(null=True, db_index=True)
    is_suspect = models.BooleanField(db_index=True)
    harmful = models.NullBooleanField(db_index=True)
    harmful_reasons = models.ManyToManyField(HarmfulReason, related_name='changesets')
    checked = models.BooleanField(default=False, db_index=True)
    check_user = models.ForeignKey(User, null=True, blank=True, db_index=True)
    check_date = models.DateTimeField(null=True, blank=True)
    objects = models.GeoManager()

    def __str__(self):
        return '%s' % self.id

    def osm_link(self):
        """Return the link to the changeset page on OSM website."""
        return 'http://www.openstreetmap.org/changeset/{}'.format(self.id)

    def viz_tool_link(self):
        """Return link to the changeset visualization tool."""
        return '{}{}'.format(settings.OSM_VIZ_TOOL_LINK, self.id)

    def josm_link(self):
        """Return link to open changeset in JOSM."""
        josm_base = "http://127.0.0.1:8111/import?url="
        changeset_url = "http://www.openstreetmap.org/api/0.6/changeset/{}/download".format(self.id)
        return "{}{}".format(josm_base, changeset_url)

    def id_link(self):
        """Return link to open the area of the changeset in iD editor."""
        id_base = "http://www.openstreetmap.org/edit?editor=id#map=16"
        if self.bbox:
            centroid = [round(c, 5) for c in self.bbox.centroid.coords]
            return "{}/{}/{}".format(id_base, centroid[1], centroid[0])
        else:
            return ""

    def to_row(self):
        reasons = self.reasons.all()
        reasons_string = ",".join(reasons.values_list('name', flat=True))
        changeset = {
            'id': self.id,
            'user': self.user,
            'editor': self.editor,
            'powerfull_editor': str(self.powerfull_editor),
            'comment': self.comment.encode('utf8') if self.comment else "",
            'source': self.source,
            'imagery_used': self.imagery_used,
            'date': self.date.strftime('%Y-%m-%d'),
            'reasons': reasons_string,
            'create': self.create,
            'modify': self.modify,
            'delete': self.delete,
            'bbox': str(self.bbox.geojson).encode('utf8'),
            'is_suspect': str(self.is_suspect),
            'harmful': str(self.harmful),
            'checked': str(self.checked),
            'check_user': self.check_user.name,
            'check_date': self.check_date.strftime('%Y-%m-%d')
            }
        return changeset

    @property
    def features(self):
        return self.feature_set.all()


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
