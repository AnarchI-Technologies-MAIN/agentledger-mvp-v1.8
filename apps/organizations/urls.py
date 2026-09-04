from django.urls import path

from .views import activate_workspace_action, workspace_selection_view

app_name = "organizations"

urlpatterns = [
    path("", workspace_selection_view, name="workspace-selection"),
    path("activate/", activate_workspace_action, name="workspace-activate"),
]
