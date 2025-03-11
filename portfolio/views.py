from rest_framework import viewsets
from .models import IndividualPortfolio
from .serializers import IndividualPortfolioSerializer

# Create your views here.


class IndividualPortfolioViewSet(viewsets.ModelViewSet):
    serializer_class = IndividualPortfolioSerializer

    def get_queryset(self):
        profile_id = self.kwargs['profile_pk']
        return IndividualPortfolio.objects.filter(profile_id=profile_id)
