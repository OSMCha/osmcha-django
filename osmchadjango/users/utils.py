# -*- coding: utf-8 -*-
from django.conf import settings

from social_django.models import UserSocialAuth

import requests


def save_real_username(backend, user, response, *args, **kwargs):
    """Function created to be part of the social_auth authentication pipeline.
    It records the real username of the OSM user in the name field of the User
    model.
    """
    if backend.name == 'openstreetmap-oauth2' and user.name != response.get('username'):
        user.name = response.get('username')
        user.save(update_fields=['name'])


def update_user_name(user):
    """Get the current username of an OSM user and update the name field of this
    user in our local database.
    """
    try:
        uid = user.social_auth.get(provider='openstreetmap-oauth2').uid
        url = f'{settings.OSM_SERVER_URL}/api/0.6/user/{uid}.json'
        data = requests.get(url, headers=settings.OSM_API_USER_AGENT).json()
        display_name = data['user']['display_name']
        if user.name != display_name:
            user.name = display_name
            user.save(update_fields=['name'])
            print('User with uid {} updated successfully.'.format(uid))
    except UserSocialAuth.DoesNotExist:
        print(
            'User {} does not have a social_auth instance.'.format(user.username)
            )
    except requests.exceptions.JSONDecodeError:
        print('It was not possible to update user with uid {}.'.format(uid))
