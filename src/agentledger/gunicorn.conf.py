from __future__ import annotations

import os

port = int(os.getenv("PORT", "8000"))
if not 1 <= port <= 65535:
    raise ValueError("PORT must be between 1 and 65535")

bind = f"0.0.0.0:{port}"
accesslog = "-"
errorlog = "-"
capture_output = True

# Deliberately excludes query strings, headers, cookies, referrers,
# and request bodies from production request logs.
access_log_format = '%(t)s %(p)s "%(m)s %(U)s %(H)s" %(s)s %(B)s %(D)s'
