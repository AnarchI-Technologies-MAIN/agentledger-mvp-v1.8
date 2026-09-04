from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.assessments.models import AssessmentSnapshot
from apps.organizations.models import Organization


class Report(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="reports",
    )
    assessment_snapshot = models.OneToOneField(
        AssessmentSnapshot,
        on_delete=models.PROTECT,
        related_name="report",
    )
    sequence = models.BigIntegerField(unique=True, editable=False)
    identifier_year = models.PositiveSmallIntegerField(editable=False)
    report_identifier = models.CharField(
        max_length=32,
        unique=True,
        editable=False,
    )
    organization_display_name = models.CharField(
        max_length=200,
        editable=False,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="generated_reports",
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        db_table = "reports"
        ordering = ("-created_at", "report_identifier")
        constraints = [
            models.CheckConstraint(
                condition=Q(sequence__gte=1),
                name="report_sequence_positive",
            ),
            models.CheckConstraint(
                condition=Q(identifier_year__gte=2000),
                name="report_identifier_year_supported",
            ),
        ]
        indexes = [
            models.Index(
                fields=("organization", "created_at"),
                name="report_org_created_idx",
            ),
        ]

    def __str__(self) -> str:
        return self.report_identifier

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Report identity records are immutable")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Report identity records are immutable")
