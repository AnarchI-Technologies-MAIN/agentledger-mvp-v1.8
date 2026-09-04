from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.organizations.models import OrganizationMember
from apps.policies.context import inventory_policy_context
from apps.policies.engine import PolicyResult, evaluate_policies
from apps.policies.packs.accounting import ACCOUNTING_RISK_PACK_V1
from apps.policies.risk import calculate_policy_risk

from .forms import InventoryItemForm
from .models import InventoryItem

WRITE_ROLES = {
    OrganizationMember.Role.OWNER,
    OrganizationMember.Role.ADMIN,
    OrganizationMember.Role.ASSESSOR,
}


def _organization_id(request):
    organization_id = getattr(request, "organization_id", None)
    if organization_id is None:
        raise Http404("Choose a firm before opening its inventory.")
    return organization_id


def _membership(request):
    return get_object_or_404(
        OrganizationMember,
        user_id=request.user.id,
        organization_id=_organization_id(request),
    )


def _require_inventory_writer(request):
    membership = _membership(request)
    if membership.role not in WRITE_ROLES:
        raise PermissionDenied("Your role has read-only access to this inventory.")
    return membership


def _inventory_item(request, item_id):
    return get_object_or_404(
        InventoryItem.objects.select_related("product__vendor"),
        id=item_id,
        organization_id=_organization_id(request),
    )


@login_required
def inventory_list_view(request):
    organization_id = _organization_id(request)
    items = InventoryItem.objects.filter(
        organization_id=organization_id,
        archived_at__isnull=True,
    )
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    if query:
        items = items.filter(
            Q(display_name__icontains=query)
            | Q(vendor_name__icontains=query)
            | Q(business_owner__icontains=query)
            | Q(department__icontains=query)
        )
    if status in InventoryItem.Status.values:
        items = items.filter(status=status)
    membership = _membership(request)
    return render(
        request,
        "inventory/list.html",
        {
            "items": items,
            "query": query,
            "selected_status": status,
            "status_choices": InventoryItem.Status.choices,
            "can_write": membership.role in WRITE_ROLES,
        },
    )


@login_required
def inventory_detail_view(request, item_id):
    item = _inventory_item(request, item_id)
    membership = _membership(request)
    policy_evaluation = evaluate_policies(
        ACCOUNTING_RISK_PACK_V1.rules,
        inventory_policy_context(item),
    )
    risk_score = calculate_policy_risk(policy_evaluation)
    return render(
        request,
        "inventory/detail.html",
        {
            "item": item,
            "can_write": membership.role in WRITE_ROLES,
            "policy_findings": tuple(
                result
                for result in policy_evaluation.results
                if result.result is not PolicyResult.NOT_APPLICABLE
            ),
            "risk_score": risk_score,
        },
    )


@login_required
def create_inventory_item_view(request):
    _require_inventory_writer(request)
    if request.method == "POST":
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.organization_id = _organization_id(request)
            item.source_type = InventoryItem.SourceType.MANUAL
            item.save()
            messages.success(request, f"{item.display_name} was added to inventory.")
            return redirect("inventory:detail", item_id=item.id)
    else:
        form = InventoryItemForm()
    return render(request, "inventory/form.html", {"form": form, "mode": "Add"})


@login_required
def edit_inventory_item_view(request, item_id):
    _require_inventory_writer(request)
    item = _inventory_item(request, item_id)
    if request.method == "POST":
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            item = form.save()
            messages.success(request, f"{item.display_name} was updated.")
            return redirect("inventory:detail", item_id=item.id)
    else:
        form = InventoryItemForm(instance=item)
    return render(request, "inventory/form.html", {"form": form, "mode": "Edit"})


@login_required
@require_POST
def archive_inventory_item_action(request, item_id):
    _require_inventory_writer(request)
    item = _inventory_item(request, item_id)
    item.archived_at = timezone.now()
    item.save(update_fields=("archived_at", "updated_at"))
    messages.success(request, f"{item.display_name} was archived.")
    return redirect("inventory:list")
