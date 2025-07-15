from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from accounts.services import metal_account_service
from accounts.serializers.metals import StorageFacilitySerializer, StorageFacilityCreateSerializer


class StorageFacilityListCreateView(APIView):
    """
    Handles:
    - GET: List storage facilities for metals
    - POST: Create new storage facility
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        facilities = metal_account_service.get_storage_facilities(request.user)
        serializer = StorageFacilitySerializer(facilities, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = StorageFacilityCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        facility = metal_account_service.create_storage_facility(request.user, serializer.validated_data)
        return Response(StorageFacilitySerializer(facility).data, status=status.HTTP_201_CREATED)
