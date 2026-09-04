from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from apps.organizations.models import Organization


class OrganizationRule(models.Model):
    class Result(models.TextChoices):
        FAIL = "FAIL", "Does not meet the rule"
        WARNING = "WARNING", "Needs attention"

    class Severity(models.TextChoices):
        LOW = "LOW", "Low"
        MODERATE = "MODERATE", "Moderate"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="policy_rules",
    )
    name = models.CharField(max_length=255)
    version = models.PositiveIntegerField(default=1, editable=False)
    enabled = models.BooleanField(default=True)
    definition = models.JSONField()
    result_on_match = models.CharField(
        max_length=16,
        choices=Result,
        default=Result.WARNING,
    )
    severity = models.CharField(
        max_length=16,
        choices=Severity,
        default=Severity.MODERATE,
    )
    explanation = models.TextField()
    remediation = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="organization_rules",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "organization_rules"
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "name"),
                name="unique_organization_rule_name",
            )
        ]
        indexes = [
            models.Index(fields=("organization",), name="organization_rule_org_idx")
        ]
        ordering = ("name", "id")

    def __str__(self) -> str:
        return f"{self.name} v{self.version}"
