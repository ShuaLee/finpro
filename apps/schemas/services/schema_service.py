from django.db import transaction


@transaction.atomic
def create_schema(model_class, portfolio, name="Default Schema"):
    """
    Generic schema creation for any portfolio type.
    Dynamically determines the correct FK relation.
    """
    relation_name = getattr(model_class, 'portfolio_relation_name', None)
    if not relation_name:
        raise ValueError("Schema model must define 'portfolio_relation_name'.")
    return model_class.objects.create(**{relation_name: portfolio}, name=name)
