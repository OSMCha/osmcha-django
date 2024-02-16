from django.contrib.gis.db import models
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.fields import JSONField
from django.utils.translation import ugettext, ugettext_lazy as _
from django.conf import settings

from ..users.models import User


class SuspicionReasons(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.CharField(max_length=1000, blank=True)
    is_visible = models.BooleanField(default=True, db_index=True)
    for_changeset = models.BooleanField(default=True)
    for_feature = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.full_clean()
        super(SuspicionReasons, self).save(*args, **kwargs)

    class Meta:
        ordering = ['id']
        verbose_name = 'Suspicion reason'
        verbose_name_plural = 'Suspicion reasons'


class Tag(models.Model):
    name = models.CharField(max_length=255, db_index=True, unique=True)
    description = models.CharField(max_length=1000, blank=True)
    is_visible = models.BooleanField(default=True, db_index=True)
    for_changeset = models.BooleanField(default=True)
    for_feature = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Tag, self).save(*args, **kwargs)

    class Meta:
        ordering = ['id']


class UserWhitelist(models.Model):
    user = models.ForeignKey(
        User, related_name='whitelists', on_delete=models.CASCADE
        )
    whitelist_user = models.CharField(max_length=1000, db_index=True)

    def __str__(self):
        return '{} whitelisted by {}'.format(self.whitelist_user, self.user)

    class Meta:
        ordering = ['-whitelist_user']
        unique_together = ('user', 'whitelist_user',)


class Changeset(models.Model):
    user = models.CharField(max_length=1000, db_index=True)
    uid = models.CharField(_('User ID'), max_length=255, blank=True, null=True)
    editor = models.CharField(max_length=255, blank=True, null=True)
    powerfull_editor = models.BooleanField(_('Powerfull Editor'), default=False)
    comment = models.CharField(max_length=1000, blank=True, null=True)
    comments_count = models.IntegerField(null=True, default=0)
    source = models.CharField(max_length=1000, blank=True, null=True)
    imagery_used = models.CharField(max_length=1000, blank=True, null=True)
    date = models.DateTimeField(null=True, db_index=True)
    reasons = models.ManyToManyField(SuspicionReasons, related_name='changesets')
    new_features = JSONField(default=list)
    reviewed_features = JSONField(default=list)
    tag_changes = JSONField(default=dict)
    create = models.IntegerField(null=True)
    modify = models.IntegerField(null=True)
    delete = models.IntegerField(null=True)
    bbox = models.PolygonField(null=True)
    area = models.FloatField(blank=True, null=True)
    is_suspect = models.BooleanField()
    harmful = models.NullBooleanField()
    tags = models.ManyToManyField(Tag, related_name='changesets')
    checked = models.BooleanField(default=False)
    check_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
        )
    check_date = models.DateTimeField(null=True, blank=True)
    metadata = JSONField(default=dict)

    def __str__(self):
        return '%s' % self.id

    def save(self, *args, **kwargs):
        # populate area field when saving object
        if self.bbox is not None:
            self.area = self.bbox.area
        super(Changeset, self).save(*args, **kwargs)

    def osm_link(self):
        """Return the link to the changeset page on OSM website."""
        return '{}/changeset/{}'.format(settings.OSM_SERVER_URL, self.id)

    def josm_link(self):
        """Return link to open changeset in JOSM."""
        josm_base = "http://127.0.0.1:8111/import?url="
        changeset_url = "{}/api/0.6/changeset/{}/download".format(
            settings.OSM_SERVER_URL,
            self.id,
            )
        return "{}{}".format(josm_base, changeset_url)

    def id_link(self):
        """Return link to open the area of the changeset in iD editor."""
        if self.bbox:
            centroid = [round(c, 5) for c in self.bbox.centroid.coords]
            return "{}/edit?editor=id#map=16/{}/{}".format(settings.OSM_SERVER_URL, centroid[1], centroid[0])
        else:
            return ""

    class Meta:
        ordering = ['-date']
        indexes = [
            GinIndex(fields=['tag_changes'])
        ]


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
