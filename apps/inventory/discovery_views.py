from __future__ import annotations

from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from collector.contract import MAX_BUNDLE_BYTES, EvidenceError

from .discovery import ingest_bundle
from .models import DiscoveryScan
from .views import _organization_id, _require_inventory_writer


class EvidenceUploadForm(forms.Form):
    bundle = forms.FileField(label="Collector evidence bundle (.json)")


@login_required
@require_http_methods(["GET", "POST"])
def discovery_view(request):
    organization_id = _organization_id(request)
    form = EvidenceUploadForm(request.POST or None, request.FILES or None)
    uploaded_scan = None
    if request.method == "POST":
        _require_inventory_writer(request)
        if form.is_valid():
            uploaded = form.cleaned_data["bundle"]
            if uploaded.size > MAX_BUNDLE_BYTES:
                form.add_error("bundle", "Evidence bundle exceeds the size limit.")
            else:
                try:
                    uploaded_scan, _created = ingest_bundle(
                        organization_id=organization_id,
                        raw=uploaded.read(MAX_BUNDLE_BYTES + 1),
                    )
                except EvidenceError as error:
                    form.add_error("bundle", str(error))
    scans = DiscoveryScan.objects.filter(organization_id=organization_id).order_by(
        "-received_at"
    )[:25]
    return render(
        request,
        "inventory/discovery.html",
        {
            "form": form,
            "scans": scans,
            "uploaded_scan": uploaded_scan,
        },
    )
