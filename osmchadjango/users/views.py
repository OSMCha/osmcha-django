# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.contrib.auth import get_user_model
from django.conf import settings

from rest_framework.authtoken.models import Token
from rest_framework.generics import RetrieveUpdateAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from social_django.utils import load_strategy, load_backend
from social_core.utils import parse_qs
import oauth2 as oauth

from .serializers import UserSerializer, SocialSignUpSerializer

User = get_user_model()


class CurrentUserDetailAPIView(RetrieveUpdateAPIView):
    """
    get:
    Get details of the current logged user.
    patch:
    Update details of the current logged user. It's allowed only to update the
    email address.
    put:
    Update details of the current logged user. It's allowed only to update the
    email address.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    model = get_user_model()
    queryset = model.objects.all()

    def get_object(self, queryset=None):
        return self.request.user


class SocialAuthView(GenericAPIView):
    queryset = User.objects.all()
    serializer_class = SocialSignUpSerializer

    base_url = 'https://www.openstreetmap.org/oauth'
    request_token_url = '{}/request_token?oauth_callback={}'.format(
        base_url,
        settings.EXTERNAL_FRONTEND_URL
        )
    access_token_url = '{}/access_token'.format(base_url)

    consumer = oauth.Consumer(
        settings.SOCIAL_AUTH_OPENSTREETMAP_KEY,
        settings.SOCIAL_AUTH_OPENSTREETMAP_SECRET
        )

    def get_access_token(self, oauth_token, oauth_token_secret, oauth_verifier):
        token = oauth.Token(oauth_token, oauth_token_secret)
        token.set_verifier(oauth_verifier)
        client = oauth.Client(self.consumer, token)
        resp, content = client.request(self.access_token_url, "POST")
        return parse_qs(content)

    def get_user_token(self, request, access_token):
        strategy = load_strategy(request)
        backend = load_backend(strategy=strategy, name='openstreetmap', redirect_uri=None)
        authed_user = request.user if not request.user.is_anonymous() else None
        user = backend.do_auth(access_token, user=authed_user)
        token, created = Token.objects.get_or_create(user=user)
        return {'token': token.key}

    def post(self, request, *args, **kwargs):
        if 'oauth_token' not in request.data.keys() or not request.data['oauth_token']:
            client = oauth.Client(self.consumer)
            resp, content = client.request(self.request_token_url, "GET")
            request_token = parse_qs(content)
            return Response({
                'oauth_token': request_token['oauth_token'],
                'oauth_token_secret': request_token['oauth_token_secret']
                })
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            access_token = self.get_access_token(
                request.data['oauth_token'],
                request.data['oauth_token_secret'],
                request.data['oauth_verifier']
                )
            return Response(self.get_user_token(request, access_token))
