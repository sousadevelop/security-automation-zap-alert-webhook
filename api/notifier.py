import json
import os
import socket
import urllib.error
import urllib.request


WEBHOOK_TIMEOUT_SECONDS = 5
MAX_ALERT_BLOCKS = 10
MAX_FIELD_LENGTH = 500


def dispatch_alert(alerts_list):
    """Send parsed ZAP alerts to the team webhook."""
    webhook_url = os.environ.get("TEAM_WEBHOOK_URL")
    alerts = alerts_list if isinstance(alerts_list, list) else []

    payload = _build_payload(alerts)

    if not webhook_url:
        return {
            "status": "skipped",
            "reason": "TEAM_WEBHOOK_URL not configured",
            "alert_count": len(alerts),
        }

    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=WEBHOOK_TIMEOUT_SECONDS) as response:
            return {
                "status": "sent",
                "code": response.getcode(),
                "alert_count": len(alerts),
            }
    except urllib.error.HTTPError as exc:
        return {
            "status": "failed",
            "reason": "http_error",
            "code": exc.code,
            "alert_count": len(alerts),
        }
    except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
        return {
            "status": "failed",
            "reason": "request_error",
            "error": str(exc),
            "alert_count": len(alerts),
        }


def _build_payload(alerts):
    risk_counts = _count_risks(alerts)
    total_alerts = len(alerts)
    critical_count = risk_counts.get("Critical", 0)
    high_count = risk_counts.get("High", 0)

    title_prefix = "🚨 CRITICAL - " if critical_count else "⚠️ "
    title = f"{title_prefix}OWASP ZAP Alert Summary"

    if not alerts:
        return {
            "content": "✅ OWASP ZAP scan processed. No High or Critical alerts found."
        }

    lines = [
        f"**{title}**",
        "",
        f"**Total alerts:** {total_alerts}",
        f"**Critical:** {critical_count}",
        f"**High:** {high_count}",
        "",
        "**Findings:**"
    ]

    for index, alert in enumerate(alerts[:MAX_ALERT_BLOCKS], start=1):
        name = _first_value(alert, "alert", "name", "title") or f"Alert {index}"
        risk = _first_value(alert, "risk", "riskdesc", "severity") or "Unknown"
        url = _first_value(alert, "url", "uri", "endpoint") or "N/A"

        lines.append(f"{index}. **{_shorten(name, 120)}**")
        lines.append(f"   - Risk: `{_shorten(risk, 60)}`")
        lines.append(f"   - URL: {_shorten(url, 180)}")

    remaining = total_alerts - MAX_ALERT_BLOCKS
    if remaining > 0:
        lines.append("")
        lines.append(f"...and {remaining} more alert(s).")

    return {
        "content": "\n".join(lines)
    }


def _alert_block(index, alert):
    if not isinstance(alert, dict):
        return {
            "type": "section",
            "title": f"Alert {index}",
            "text": _shorten(str(alert)),
        }

    name = _first_value(alert, "alert", "name", "title") or f"Alert {index}"
    risk = _first_value(alert, "risk", "riskdesc", "severity") or "Unknown"
    url = _first_value(alert, "url", "uri", "endpoint")
    parameter = _first_value(alert, "param", "parameter")
    description = _first_value(alert, "description", "desc", "message")

    fields = {
        "risk": _shorten(risk, 120),
    }

    if url:
        fields["url"] = _shorten(url, 240)
    if parameter:
        fields["parameter"] = _shorten(parameter, 120)
    if description:
        fields["description"] = _shorten(description)

    return {
        "type": "section",
        "title": _shorten(name, 160),
        "fields": fields,
    }


def _count_risks(alerts):
    counts = {}
    for alert in alerts:
        if not isinstance(alert, dict):
            counts["Unknown"] = counts.get("Unknown", 0) + 1
            continue

        raw_risk = _first_value(alert, "risk", "riskdesc", "severity") or "Unknown"
        risk = _normalize_risk(raw_risk)
        counts[risk] = counts.get(risk, 0) + 1

    return counts


def _normalize_risk(value):
    text = str(value).strip()
    lowered = text.lower()

    if "critical" in lowered:
        return "Critical"
    if "high" in lowered:
        return "High"
    if "medium" in lowered:
        return "Medium"
    if "low" in lowered:
        return "Low"
    if "informational" in lowered or "info" in lowered:
        return "Informational"

    return text.title() if text else "Unknown"


def _first_value(mapping, *keys):
    for key in keys:
        value = mapping.get(key)
        if value is not None and value != "":
            return str(value)
    return None


def _shorten(value, limit=MAX_FIELD_LENGTH):
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."
