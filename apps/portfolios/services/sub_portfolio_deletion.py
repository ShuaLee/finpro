from django.contrib.contenttypes.models import ContentType
from schemas.models import Schema

def delete_subportfolio_with_schema(portfolio):
    """
    Deletes a subportfolio and its associated schema.
    """
    ct = ContentType.objects.get_for_model(portfolio.__class__)
    Schema.objects.filter(content_type=ct, object_id=portfolio.id).delete()
    portfolio.delete()