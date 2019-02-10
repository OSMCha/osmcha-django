# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.postgres.fields import JSONField


class User(AbstractUser):
    # First Name and Last Name do not cover name patterns around the globe.
    name = models.CharField(
        "Name of User", blank=True, max_length=255, db_index=True
        )
    message_good = models.TextField(
        "Default message to good changesets",
        blank=True
        )
    message_bad = models.TextField(
        "Default message to bad changesets",
        blank=True
        )
    comment_feature = models.BooleanField(
        "Enable suggestion to post comment",
        default=False
        )

    def __str__(self):
        return self.username


class MappingTeam(models.Model):
    name = models.CharField(max_length=255, db_index=True, unique=True)
    date = models.DateTimeField("Creation Date", auto_now_add=True)
    trusted = models.BooleanField(default=False)
    users = JSONField(default=list)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return '{} by {}'.format(self.name, self.created_by.username)

    class Meta:
        ordering = ['date']
        verbose_name = 'Mapping Team'
        verbose_name_plural = 'Mapping Teams'
