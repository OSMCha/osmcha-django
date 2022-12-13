import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError

from social_django.models import UserSocialAuth

import requests


def save_real_username(backend, user, response, *args, **kwargs):
    """Function created to be part of the social_auth authentication pipeline.
    It records the real username of the OSM user in the name field of the User
    model.
    """
    if backend.name == "openstreetmap" and user.name != response.get("username"):
        user.name = response.get("username")
        user.save(update_fields=["name"])


def update_user_name(user):
    """Get the current username of an OSM user and update the name field of this
    user in our local database.
    """
    try:
        uid = user.social_auth.get(provider="openstreetmap").uid
        url = f"https://www.openstreetmap.org/api/0.6/user/{uid}/"
        data = ET.fromstring(requests.get(url).content)
        display_name = data.find("user").get("display_name")
        if user.name != display_name:
            user.name = display_name
            user.save(update_fields=["name"])
            print(f"User with uid {uid} updated successfully.")
    except UserSocialAuth.DoesNotExist:
        print(f"User {user.username} does not have a social_auth instance.")
    except ParseError:
        print(f"It was not possible to update user with uid {uid}.")
