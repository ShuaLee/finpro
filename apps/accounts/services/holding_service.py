# from django.db import transaction
# from django.core.exceptions import ValidationError
# from accounts.models.account import Account
# from holdings.models import Holding  # assuming you have a generic Holding model
# from schemas.services.schema_manager import SchemaManager


# class HoldingsService:
#     """
#     Service layer for managing holdings tied to accounts.
#     """

#     @staticmethod
#     @transaction.atomic
#     def create_holding(account: Account, asset, quantity: float, purchase_price: float = None, **extra_fields):
#         """
#         Create a new holding under an account.

#         Args:
#             account (Account): The parent account.
#             asset (Asset): The linked asset object (stock, crypto, metal, etc.).
#             quantity (float): Quantity purchased/held.
#             purchase_price (float, optional): Price at which it was acquired.
#             extra_fields (dict): Additional holding-specific fields.

#         Returns:
#             Holding
#         """
#         holding = Holding.objects.create(
#             account=account,
#             asset=asset,
#             quantity=quantity,
#             purchase_price=purchase_price,
#             **extra_fields,
#         )

#         # Sync schema column values for this holding
#         SchemaManager.ensure_for_holding(holding)

#         return holding

#     @staticmethod
#     @transaction.atomic
#     def delete_holding(holding: Holding):
#         """
#         Delete a holding and clean up associated schema values.
#         """
#         # Remove schema column values
#         SchemaManager.delete_for_holding(holding)

#         holding.delete()

#     @staticmethod
#     def get_current_value(holding: Holding):
#         """
#         Calculate current value of a holding.
#         (Delegates to holding model, but can enforce validation here.)
#         """
#         if not hasattr(holding, "get_current_value"):
#             raise ValidationError("Holding model must implement get_current_value().")
#         return holding.get_current_value()

#     @staticmethod
#     def recalc_account_value(account: Account):
#         """
#         Recalculate total value of all holdings in an account.
#         """
#         total = 0
#         for holding in account.holdings.all():
#             val = HoldingsService.get_current_value(holding)
#             if val:
#                 total += val
#         return total
