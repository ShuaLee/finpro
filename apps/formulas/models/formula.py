from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

import ast


ALLOWED_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.UAdd,
    ast.USub,
    ast.Name,
    ast.Load,
    ast.Constant,
)


class Formula(models.Model):
    """
    Pure mathematical formula.

    - Contains NO schema knowledge
    - Contains NO asset-type knowledge
    - Dependencies are DERIVED from expression
    """

    owner = models.ForeignKey(
        "users.Profile",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="formulas",
        help_text="Null = system formula, otherwise user-owned."
    )

    title = models.CharField(
        max_length=100,
        blank=True,
        help_text="Human-readable formula name."
    )

    identifier = models.SlugField(
        max_length=100,
        help_text="Stable snake_case identifier."
    )

    expression = models.TextField(
        help_text="Python-style mathematical expression."
    )

    dependencies = models.JSONField(
        default=list,
        editable=False,
        help_text="Derived identifiers referenced by this formula."
    )

    decimal_places = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Optional precision override."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["identifier"]
        constraints = [
            models.UniqueConstraint(
                fields=["identifier", "owner"],
                name="uniq_formula_identifier_per_owner",
            )
        ]

    def clean(self):
        super().clean()

        if not self.expression:
            raise ValidationError("Formula expression is required.")

        try:
            tree = ast.parse(self.expression, mode="eval")
        except SyntaxError as exc:
            raise ValidationError(f"Invalid formula syntax: {exc}")

        referenced = set()

        for node in ast.walk(tree):
            if not isinstance(node, ALLOWED_NODES):
                raise ValidationError(
                    f"Unsupported expression element: {type(node).__name__}"
                )

            if isinstance(node, ast.Name):
                referenced.add(node.id)

        if self.identifier in referenced:
            raise ValidationError("Formula cannot reference itself.")

        # Source of truth → AST
        self.dependencies = sorted(referenced)

    def save(self, *args, **kwargs):
        if not self.identifier:
            raise ValidationError("Identifier is required.")

        self.identifier = slugify(self.identifier)
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        scope = "system" if self.owner is None else f"user={self.owner_id}"
        return f"Formula({self.identifier}, {scope})"
