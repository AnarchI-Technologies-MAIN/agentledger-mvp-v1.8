from django.urls import path

from .views import generate_report_action, report_detail_view

app_name = "reports"

urlpatterns = [
    path(
        "from-assessment/<uuid:snapshot_id>/",
        generate_report_action,
        name="generate",
    ),
    path("<uuid:report_id>/", report_detail_view, name="detail"),
]
