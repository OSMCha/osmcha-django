# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.contrib.auth import get_user_model

from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from .serializers import UserSerializer


class CurrentUserDetailAPIView(RetrieveUpdateAPIView):
    """Get or update details of the current logged user. It's allowed only to
    update the email address.
    """
    permission_classes = IsAuthenticated,
    serializer_class = UserSerializer
    model = get_user_model()
    queryset = model.objects.all()

    def get_object(self, queryset=None):
        return self.request.user
