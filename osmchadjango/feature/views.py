import json
from datetime import datetime

from django.utils import timezone
from django.db import IntegrityError
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.gdal.error import GDALException

import django_filters.rest_framework
from rest_framework.generics import (
    ListAPIView, RetrieveAPIView, get_object_or_404
    )
from rest_framework.decorators import (
    api_view, parser_classes, permission_classes, throttle_classes
    )
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework import status
from rest_framework_gis.filters import InBBoxFilter

from osmchadjango.changeset import models as changeset_models

from ..changeset.views import StandardResultsSetPagination, PaginatedCSVRenderer
from ..changeset.views import NonStaffUserThrottle
from .models import Feature
from .serializers import FeatureSerializer, FeatureSerializerToStaff
from .filters import FeatureFilter


class FeatureListAPIView(ListAPIView):
    """List Features. It can be filtered using the 'location' parameter, which can
    receive any valid geometry, or using the 'in_bbox' field, which must receive
    the min Lat, min Lon, max Lat, max Lon values. It's also possible to filter
    using other fields. The default pagination return 50 objects by page.
    """
    queryset = Feature.objects.all().select_related(
        'check_user', 'changeset'
        ).prefetch_related('reasons', 'tags')
    serializer_class = FeatureSerializer
    pagination_class = StandardResultsSetPagination
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer, PaginatedCSVRenderer)
    bbox_filter_field = 'geometry'
    filter_backends = (
        InBBoxFilter,
        django_filters.rest_framework.DjangoFilterBackend,
        )
    bbox_filter_include_overlapping = True
    filter_class = FeatureFilter

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return FeatureSerializerToStaff
        else:
            return FeatureSerializer


class FeatureDetailAPIView(RetrieveAPIView):
    '''Get details of a Feature object. Type: GeoJSON'''
    queryset = Feature.objects.all().select_related(
        'check_user', 'changeset'
        ).prefetch_related('reasons', 'tags')

    def get_object(self):
        changeset = self.kwargs['changeset']
        url = self.kwargs['slug']
        return get_object_or_404(Feature, changeset=changeset, url=url)

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return FeatureSerializerToStaff
        else:
            return FeatureSerializer


@api_view(['POST'])
@parser_classes((JSONParser, MultiPartParser, FormParser))
@permission_classes((IsAuthenticated, IsAdminUser))
def create_feature(request):
    '''Create Suspicion Features. It was designed to receive vandalism-dynamosm
    json output. Only staff users have permissions to create features. You can
    use the django admin to get a Token to the user you want to use to created
    features.
    '''
    feature = request.data

    if 'properties' not in feature.keys():
        return Response(
            {'message': 'Expecting a single GeoJSON feature.'},
            status=status.HTTP_400_BAD_REQUEST
            )
    properties = feature.get('properties', {})
    changeset_id = properties.get('osm:changeset')

    if not changeset_id:
        return Response(
            {'message': 'osm:changeset field is missing.'},
            status=status.HTTP_400_BAD_REQUEST
            )

    defaults = {
        'osm_id': properties['osm:id'],
        'osm_type': properties['osm:type'],
        'url': '{}-{}'  .format(properties['osm:type'], properties['osm:id']),
        'osm_version': properties['osm:version'],
        'comparator_version': feature.get('comparator_version'),
        }

    try:
        defaults['geometry'] = GEOSGeometry(json.dumps(feature['geometry']))
    except (GDALException, ValueError, TypeError) as e:
        return Response(
            {'message': '{} in geometry field of feature {}'.format(e, properties['osm:id'])},
            status=status.HTTP_400_BAD_REQUEST
            )

    if 'oldVersion' in properties.keys():
        try:
            defaults['old_geometry'] = GEOSGeometry(
                json.dumps(properties['oldVersion']['geometry'])
                )
        except (GDALException, ValueError, TypeError) as e:
            print(
                '{} in oldVersion.geometry field of feature {}'.format(
                    e, properties['osm:id']
                    )
                )
        defaults['old_geojson'] = feature['properties'].pop('oldVersion')

    # Each changed feature should have a 'suspicions' array of objects in its properties
    suspicions = feature['properties'].pop('suspicions')
    has_visible_features = False
    if suspicions:
        reasons = set()
        for suspicion in suspicions:
            if suspicion.get('is_visible') is False:
                is_visible = False
            else:
                has_visible_features = True
                is_visible = True
            reason, created = changeset_models.SuspicionReasons.objects.get_or_create(
                name=suspicion['reason'],
                defaults={'is_visible': is_visible}
                )
            reasons.add(reason)

    changeset_defaults = {
        'date': datetime.utcfromtimestamp(properties.get('osm:timestamp') / 1000),
        'uid': properties.get('osm:uid'),
        'is_suspect': has_visible_features
        }

    changeset, created = changeset_models.Changeset.objects.get_or_create(
        id=changeset_id,
        defaults=changeset_defaults
        )

    if not changeset.is_suspect and has_visible_features:
        changeset.is_suspect = True
        changeset.save(update_fields=['is_suspect'])

    try:
        changeset.reasons.add(*reasons)
    except IntegrityError:
        # This most often happens due to a race condition,
        # where two processes are saving to the same changeset
        # In this case, we can safely ignore this attempted DB Insert,
        # since what we wanted inserted has already been done through
        # a separate web request.
        print('IntegrityError with changeset %s' % changeset_id)
    except ValueError as e:
        print('ValueError with changeset %s' % changeset_id)

    defaults['geojson'] = feature
    suspicious_feature, created = Feature.objects.get_or_create(
        osm_id=properties['osm:id'],
        changeset=changeset,
        defaults=defaults
        )

    try:
        suspicious_feature.reasons.add(*reasons)
    except IntegrityError:
        # This most often happens due to duplicates in dynamosm stream
        print('Integrity error with feature %s' % suspicious_feature.osm_id)
    except ValueError as e:
        print('Value error with feature %s' % suspicious_feature.osm_id)

    return Response(
        {'message': 'Feature created.'},
        status=status.HTTP_201_CREATED
        )


@api_view(['PUT'])
@throttle_classes((NonStaffUserThrottle,))
@parser_classes((JSONParser, MultiPartParser, FormParser))
@permission_classes((IsAuthenticated,))
def set_harmful_feature(request, changeset, slug):
    """Mark a feature as harmful. You can set the tags of the feature by sending
    a list of tag ids inside a field named 'tags' in the request data. If you
    don't want to set the 'tags', you don't need to send data, just make an
    empty PUT request.
    """
    instance = get_object_or_404(Feature, changeset=changeset, url=slug)
    user_uids = request.user.social_auth.values_list('uid', flat=True)
    if instance.changeset.uid not in user_uids:
        if instance.checked is False:
            instance.checked = True
            instance.harmful = True
            instance.check_user = request.user
            instance.check_date = timezone.now()
            instance.save(
                update_fields=['checked', 'harmful', 'check_user', 'check_date']
                )
            if 'tags' in request.data.keys():
                ids = [int(i) for i in request.data.pop('tags')]
                tags = changeset_models.Tag.objects.filter(
                    id__in=ids
                    )
                instance.tags.set(tags)
            return Response(
                {'message': 'Feature marked as harmful.'},
                status=status.HTTP_200_OK
                )
        else:
            return Response(
                {'message': 'Feature could not be updated.'},
                status=status.HTTP_403_FORBIDDEN
                )
    else:
        return Response(
            {'message': 'User does not have permission to update this feature.'},
            status=status.HTTP_403_FORBIDDEN
            )


@api_view(['PUT'])
@throttle_classes((NonStaffUserThrottle,))
@parser_classes((JSONParser, MultiPartParser, FormParser))
@permission_classes((IsAuthenticated,))
def set_good_feature(request, changeset, slug):
    """Mark a feature as good. You can set the tags of the feature by sending
    a list of tag ids inside a field named 'tags' in the request data. If you
    don't want to set the 'tags', you don't need to send data, just make an
    empty PUT request.
    """
    instance = get_object_or_404(Feature, changeset=changeset, url=slug)
    user_uids = request.user.social_auth.values_list('uid', flat=True)
    if instance.changeset.uid not in user_uids:
        if instance.checked is False:
            instance.checked = True
            instance.harmful = False
            instance.check_user = request.user
            instance.check_date = timezone.now()
            instance.save(
                update_fields=['checked', 'harmful', 'check_user', 'check_date']
                )
            if 'tags' in request.data.keys():
                ids = [int(i) for i in request.data.pop('tags')]
                tags = changeset_models.Tag.objects.filter(
                    id__in=ids
                    )
                instance.tags.set(tags)
            return Response(
                {'message': 'Feature marked as good.'},
                status=status.HTTP_200_OK
                )
        else:
            return Response(
                {'message': 'Feature could not be updated.'},
                status=status.HTTP_403_FORBIDDEN
                )
    else:
        return Response(
            {'message': 'User does not have permission to update this feature.'},
            status=status.HTTP_403_FORBIDDEN
            )


@api_view(['PUT'])
@parser_classes((JSONParser, MultiPartParser, FormParser))
@permission_classes((IsAuthenticated,))
def uncheck_feature(request, changeset, slug):
    """Mark a feature as unchecked. You don't need to send data, just an empty
    PUT request.
    """
    instance = get_object_or_404(Feature, changeset=changeset, url=slug)
    if instance.checked is False:
        return Response(
            {'message': 'Feature is not checked.'},
            status=status.HTTP_403_FORBIDDEN
            )
    elif request.user == instance.check_user:
        instance.checked = False
        instance.harmful = None
        instance.check_user = None
        instance.check_date = None
        instance.save(
            update_fields=['checked', 'harmful', 'check_user', 'check_date']
            )
        instance.tags.clear()
        return Response(
            {'message': 'Feature marked as unchecked.'},
            status=status.HTTP_200_OK
            )
    else:
        return Response(
            {'message': 'User does not have permission to uncheck this feature.'},
            status=status.HTTP_403_FORBIDDEN
            )
