from django.contrib.auth import get_user_model

from rest_framework.serializers import ModelSerializer


class UserSerializer(ModelSerializer):
    class Meta:
        model = get_user_model()
        exclude = ('first_name', 'last_name', 'name', 'date_joined', 'password',
            'last_login', 'is_superuser', 'user_permissions', 'groups')
        read_only_fields = ('username', 'password', 'is_staff', 'is_active')