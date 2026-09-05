from __future__ import annotations

from django.db import transaction

from collector.contract import fingerprint, timestamp, validate_bundle

from .models import DetectionEvidence, DiscoveryScan


def ingest_bundle(*, organization_id, raw: bytes):
    """Persist bounded Collector-reported observations without changing inventory."""
    bundle = validate_bundle(raw)
    with transaction.atomic():
        scan, created = DiscoveryScan.objects.get_or_create(
            organization_id=organization_id,
            scan_hash=bundle["scan_id"],
            defaults={
                "device_id": bundle["device_id"],
                "observed_at": timestamp(bundle["observed_at"]),
                "bundle": bundle,
            },
        )
        if created:
            DetectionEvidence.objects.bulk_create(
                [
                    DetectionEvidence(
                        organization_id=organization_id,
                        scan=scan,
                        fingerprint=fingerprint(record),
                        evidence_hash=record["evidence_hash"],
                        record=record,
                    )
                    for record in bundle["evidence"]
                ]
            )
    return scan, created
