from __future__ import annotations

import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.organizations.models import Organization


class InventoryItem(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        TRIAL = "trial", "Trial"
        INACTIVE = "inactive", "Inactive"
        REVIEWING = "reviewing", "Reviewing"

    class SourceType(models.TextChoices):
        MANUAL = "manual", "Entered by a person"
        CSV = "csv", "Imported from a spreadsheet"
        DISCOVERED = "discovered", "Discovered from a connected source"

    class Autonomy(models.IntegerChoices):
        NONE = 0, "It does not act on its own"
        SUGGESTS = 1, "It suggests actions for a person to take"
        AFTER_APPROVAL = 2, "It acts only after a person approves"
        LIMITED_AUTOMATIC = 3, "It can perform some tasks on its own"
        SIGNIFICANT_AUTOMATIC = 4, "It can perform important tasks on its own"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="inventory_items",
    )
    product_id = models.UUIDField(null=True, blank=True)
    display_name = models.CharField(max_length=255)
    vendor_name = models.CharField(max_length=255)
    business_owner = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=255, blank=True)
    user_count = models.PositiveIntegerField(default=0)
    business_purpose = models.TextField(blank=True)
    monthly_cost_cents = models.PositiveIntegerField(default=0)
    seat_count = models.PositiveIntegerField(default=0)
    connected_systems = models.JSONField(default=list, blank=True)
    data_categories = models.JSONField(default=list, blank=True)
    permissions = models.JSONField(default=list, blank=True)
    capabilities = models.JSONField(default=list, blank=True)
    autonomy_level = models.PositiveSmallIntegerField(
        choices=Autonomy,
        default=Autonomy.NONE,
        validators=[MinValueValidator(0), MaxValueValidator(4)],
    )
    human_approval = models.BooleanField(default=True)
    status = models.CharField(max_length=16, choices=Status, default=Status.REVIEWING)
    source_type = models.CharField(
        max_length=16,
        choices=SourceType,
        default=SourceType.MANUAL,
    )
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventory_items"
        indexes = [
            models.Index(fields=("organization",), name="inventory_org_idx"),
            models.Index(
                fields=("organization", "status"),
                name="inventory_org_status_idx",
            ),
        ]
        ordering = ("display_name", "id")

    def __str__(self) -> str:
        return self.display_name
