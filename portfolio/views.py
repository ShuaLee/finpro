from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet
from .models import IndividualPortfolio
from .serializers import IndividualPortfolioSerializer

# Create your views here.


class IndividualPortfolioViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    serializer_class = IndividualPortfolioSerializer

    def get_queryset(self):
        profile_id = self.kwargs['profile_pk']
        return IndividualPortfolio.objects.filter(profile_id=profile_id)

    def get_object(self):
        """
        Retrieve the single IndividualPortfolio for the given profile.
        """
        profile_id = self.kwargs['profile_pk']
        return IndividualPortfolio.objects.get(profile_id=profile_id)
