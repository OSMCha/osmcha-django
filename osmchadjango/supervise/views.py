from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from .models import AreaOfInterest
from .serializers import AreaOfInterestSimpleSerializer


class AOIListCreateAPIView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = AreaOfInterestSimpleSerializer

    def get_queryset(self):
        return AreaOfInterest.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
