from __future__ import annotations

from uuid import UUID

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.inventory.models import InventoryItem
from apps.organizations.models import Organization

DEMO_ITEMS = (
    ("QuickBooks Online", "Intuit", "Accounting", 8000, 8, 1),
    ("Microsoft 365 Copilot", "Microsoft", "Operations", 24000, 8, 1),
    ("ChatGPT Team", "OpenAI", "Advisory", 15000, 5, 1),
    ("Dext Prepare", "Dext", "Bookkeeping", 30000, 12, 2),
    ("Gusto", "Gusto", "Payroll", 18000, 4, 2),
    ("Bill.com", "BILL", "Accounts payable", 22000, 6, 2),
    ("Dropbox Sign", "Dropbox", "Administration", 6000, 3, 1),
    ("HubSpot", "HubSpot", "Client service", 9000, 5, 3),
    ("Zapier", "Zapier", "Operations", 12000, 2, 3),
    ("Canva", "Canva", "Marketing", 4500, 3, 1),
)


class Command(BaseCommand):
    help = "Create the bounded ten-item bookkeeping demonstration inventory."

    def add_arguments(self, parser):
        parser.add_argument("organization_id", type=str)

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            organization_id = UUID(options["organization_id"])
        except (TypeError, ValueError) as error:
            raise CommandError("organization_id must be a UUID") from error

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist as error:
            raise CommandError("The organization does not exist") from error

        if InventoryItem.objects.filter(organization=organization).exists():
            raise CommandError("Demo inventory requires an organization with no items")

        InventoryItem.objects.bulk_create(
            [
                InventoryItem(
                    organization=organization,
                    display_name=name,
                    vendor_name=vendor,
                    department=department,
                    business_owner="Demo operations lead",
                    business_purpose="Demonstration bookkeeping workflow",
                    monthly_cost_cents=monthly_cost,
                    user_count=users,
                    seat_count=users,
                    autonomy_level=autonomy,
                    human_approval=True,
                    status=InventoryItem.Status.ACTIVE,
                    source_type=InventoryItem.SourceType.MANUAL,
                )
                for name, vendor, department, monthly_cost, users, autonomy in (
                    DEMO_ITEMS
                )
            ]
        )
        self.stdout.write(
            self.style.SUCCESS("Created 10 demonstration inventory items.")
        )
