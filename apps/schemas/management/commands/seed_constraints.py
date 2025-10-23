from django.core.management.base import BaseCommand

from schemas.config.constraints_template import CONSTRAINT_TEMPLATES
from schemas.models.constraints import MasterConstraint


class Command(BaseCommand):
    help = "Seed MasterConstraint records from CONSTRAINT_TEMPLATES."

    def handle(self, *args, **kwargs):
        for data_type, templates in CONSTRAINT_TEMPLATES.items():
            for t in templates:
                obj, created = MasterConstraint.objects.update_or_create(
                    applies_to=data_type,
                    name=t["name"],
                    defaults={
                        "label": t["label"],
                        "default_value": t.get("default"),
                        "min_limit": t.get("min"),
                        "max_limit": t.get("max"),
                        "is_editable": t.get("editable", True),
                        "is_active": True,
                    },
                )
                action = "Created" if created else "Updated"
                self.stdout.write(f"{action} MasterConstraint: {obj}")