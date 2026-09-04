from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.assessments.models import AssessmentSnapshot
from apps.organizations.models import OrganizationMember

from .context import build_report_context
from .models import Report
from .services import create_report

WRITE_ROLES = {
    OrganizationMember.Role.OWNER,
    OrganizationMember.Role.ADMIN,
    OrganizationMember.Role.ASSESSOR,
}


def _organization_id(request):
    organization_id = getattr(request, "organization_id", None)
    if organization_id is None:
        raise Http404("Choose a firm before opening a report.")
    return organization_id


@login_required
@require_POST
@transaction.atomic
def generate_report_action(request, snapshot_id):
    organization_id = _organization_id(request)
    membership = get_object_or_404(
        OrganizationMember,
        organization_id=organization_id,
        user_id=request.user.id,
    )
    if membership.role not in WRITE_ROLES:
        raise PermissionDenied("Your role has read-only access to reports.")
    snapshot = get_object_or_404(
        AssessmentSnapshot,
        id=snapshot_id,
        organization_id=organization_id,
    )
    report = create_report(
        organization_id=organization_id,
        assessment_snapshot_id=snapshot.id,
        created_by_id=request.user.id,
    )
    return redirect("reports:detail", report_id=report.id)


@login_required
def report_detail_view(request, report_id):
    report = get_object_or_404(
        Report.objects.select_related("assessment_snapshot"),
        id=report_id,
        organization_id=_organization_id(request),
    )
    return render(
        request,
        "reports/detail.html",
        {"report": build_report_context(report)},
    )
