from django.db import models
from django.contrib.auth import get_user_model

from ..changeset.models import SuspicionReasons

User = get_user_model()


class ChallengeIntegration(models.Model):
    challenge_id = models.IntegerField(unique=True, db_index=True)
    reasons = models.ManyToManyField(SuspicionReasons, related_name='challenges')
    active = models.BooleanField(default=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, related_name="challenges", on_delete=models.CASCADE)

    def __str__(self):
        return 'Challenge {}'.format(self.challenge_id)

    class Meta:
        ordering = ['id']
        verbose_name = 'Challenge Integration'
        verbose_name_plural = 'Challenge Integrations'
