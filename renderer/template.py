from __future__ import annotations

from pathlib import Path
from typing import Any

from django.template import Context, Engine

TEMPLATE_DIRECTORY = Path(__file__).resolve().parent / "templates"
_ENGINE = Engine(dirs=(TEMPLATE_DIRECTORY,), autoescape=True, debug=False)


def render_report_html(payload: dict[str, Any]) -> str:
    template = _ENGINE.get_template("report.html")
    return template.render(
        Context(
            {"report": payload},
            autoescape=True,
            use_l10n=False,
            use_tz=False,
        )
    )
