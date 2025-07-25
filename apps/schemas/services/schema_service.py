from django.db import transaction


@transaction.atomic
def create_schema(model_class, portfolio, name="Default Schema"):
    """
    Generic schema creation for any portfolio type.
    :param model_class: Schema model class (e.g., StockPortfolioSchema)
    :param portfolio: Portfolio instance (e.g., StockPortfolio)
    :param name: Name for the schema
    """
    relation_name = model_class.portfolio_relation_name if hasattr(
        model_class, 'portfolio_relation_name') else None
    if not relation_name:
        # Default fallback if portfolio_relation_name is not available on the class
        relation_name = 'stock_portfolio'

    return model_class.objects.create(**{relation_name: portfolio}, name=name)
