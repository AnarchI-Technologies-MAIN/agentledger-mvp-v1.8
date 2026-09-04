from __future__ import annotations

from uuid import UUID

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from agentledger.tenancy.context import identity_transaction

from .models import OrganizationMember


@login_required
def workspace_selection_view(request):
    with identity_transaction(request.user.id):
        memberships = list(
            OrganizationMember.objects.filter(user_id=request.user.id)
            .select_related("organization")
            .order_by("organization__name", "organization_id")
        )

    return render(
        request,
        "organizations/select_workspace.html",
        {
            "memberships": memberships,
            "active_organization_id": request.session.get("active_organization_id"),
        },
    )


@login_required
@require_POST
def activate_workspace_action(request):
    raw_id = request.POST.get("organization_id")
    try:
        organization_id = UUID(str(raw_id))
    except (TypeError, ValueError, AttributeError) as error:
        raise PermissionDenied("The selected workspace is invalid.") from error

    with identity_transaction(request.user.id):
        membership = (
            OrganizationMember.objects.filter(
                user_id=request.user.id,
                organization_id=organization_id,
            )
            .select_related("organization")
            .first()
        )

    if membership is None:
        request.session.pop("active_organization_id", None)
        raise PermissionDenied("You do not have access to this workspace.")

    request.session["active_organization_id"] = str(organization_id)
    messages.success(request, f"Now working in {membership.organization.name}.")
    return redirect("organizations:workspace-selection")
