# -*- coding: utf-8 -*-
import logging

from django.conf import settings

from social_django.models import UserSocialAuth

import requests

logger = logging.getLogger(__name__)


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
            logger.info('User with uid %s updated successfully.', uid)
    except UserSocialAuth.DoesNotExist:
        logger.warning(
            'User %s does not have a social_auth instance.', user.username
            )
    except requests.exceptions.JSONDecodeError:
        logger.warning('It was not possible to update user with uid %s.', uid)
