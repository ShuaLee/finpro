from django.db import transaction


@transaction.atomic
def create_schema(model_class, portfolio, name="Default Schema"):
    """
    Generic schema creation for any portfolio type.
    Relies on `relation_name` class attribute for FK field.
    """
    if not hasattr(model_class, "relation_name"):
        raise ValueError(
            f"{model_class.__name__} must define 'relation_name' class attribute.")

    relation_name = model_class.relation_name
    return model_class.objects.create(**{relation_name: portfolio}, name=name)
