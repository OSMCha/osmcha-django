from django.db import models

from osmchadjango.changeset.models import Changeset


class Priority(models.Model):
    changeset = models.OneToOneField(Changeset)

    def __str__(self):
        return 'Changeset {}'.format(self.changeset.id)

    class Meta:
        verbose_name_plural = 'Priorities'
