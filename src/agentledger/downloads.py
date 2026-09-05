from django.shortcuts import render

COLLECTOR_RELEASE = {
    "version": "0.1.0",
    "asset_name": "Stewardence-Collector-Windows-x64-v0.1.0.zip",
    "asset_url": (
        "https://github.com/AnarchI-Technologies-MAIN/"
        "stewardence-mvp-v1.8/releases/download/collector-v0.1.0/"
        "Stewardence-Collector-Windows-x64-v0.1.0.zip"
    ),
    "sha256": "fe7239402a29aa2bf4e732b2de4f9533ba240ddd0d7d46386d0d659926b57b3a",
    "executable_sha256": (
        "e8228a6cccd79c47f427be3f01ef7973b94a5a0ab71d87c27ba7abf3df1ef00c"
    ),
    "profile_sha256": (
        "d71d6d65d359f70ada3c04ed31e60dea1d9f73f53b2a3be1677225ef7e27d12a"
    ),
    "public_key_sha256": (
        "c6208fe13ee170ca940752100c053625b82c6b63bdad1f3a660ff7e7e841ae4f"
    ),
    "available_module": "Windows Installed Programs",
}

POST_MVP_MODULES = (
    "Microsoft 365 Intelligence",
    "Google Workspace Intelligence",
    "GitHub Intelligence",
    "Accounting Intelligence",
    "Browser Intelligence",
    "Developer Tooling Intelligence",
    "Continuous Observation",
    "Desktop Portal",
)


def download_view(request):
    return render(
        request,
        "downloads/detail.html",
        {
            "release": COLLECTOR_RELEASE,
            "post_mvp_modules": POST_MVP_MODULES,
        },
    )
