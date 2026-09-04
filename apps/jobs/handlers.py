from __future__ import annotations

from collections.abc import Callable

from apps.audit.jobs import AuditBatchSealHandler
from apps.jobs.models import BackgroundJob
from apps.jobs.worker import JobHandler


class UnsupportedJobHandler(ValueError):
    pass


def build_job_handler_resolver(
    *,
    using: str = "default",
) -> Callable[[str], JobHandler]:
    audit_batch_seal_handler = AuditBatchSealHandler(
        using=using,
    )

    def resolve(job_type: str) -> JobHandler:
        if job_type == BackgroundJob.Type.AUDIT_BATCH_SEAL:
            return audit_batch_seal_handler

        raise UnsupportedJobHandler(f"No job handler is registered for {job_type}")

    return resolve
