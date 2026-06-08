"""Utilities for extracting high-risk alerts from OWASP ZAP JSON reports."""


RISK_LEVELS = {
    "0": "Informational",
    "1": "Low",
    "2": "Medium",
    "3": "High",
    "4": "Critical",
    "informational": "Informational",
    "info": "Informational",
    "low": "Low",
    "medium": "Medium",
    "high": "High",
    "critical": "Critical",
}

TARGET_RISKS = {"High", "Critical"}


def _as_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, dict):
        return [value]
    return []


def _first_present(*values):
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _normalize_risk(alert):
    raw_risk = _first_present(
        alert.get("risk"),
        alert.get("riskdesc"),
        alert.get("riskDesc"),
        alert.get("riskcode"),
        alert.get("riskCode"),
    )

    if raw_risk is None:
        return None

    risk = str(raw_risk).strip()
    if not risk:
        return None

    risk_key = risk.split("(", 1)[0].strip().lower()
    return RISK_LEVELS.get(risk_key, risk_key.capitalize())


def _normalize_instance(instance):
    return {
        key: value
        for key, value in {
            "url": _first_present(instance.get("url"), instance.get("uri")),
            "method": instance.get("method"),
            "param": instance.get("param"),
            "attack": instance.get("attack"),
            "evidence": instance.get("evidence"),
            "otherinfo": _first_present(instance.get("otherinfo"), instance.get("other")),
        }.items()
        if value not in (None, "")
    }


def _extract_alerts(json_data):
    if not isinstance(json_data, dict):
        return []

    alerts = []
    for site in _as_list(json_data.get("site")):
        if isinstance(site, dict):
            alerts.extend(alert for alert in _as_list(site.get("alerts")) if isinstance(alert, dict))

    alerts.extend(alert for alert in _as_list(json_data.get("alerts")) if isinstance(alert, dict))
    return alerts


def parse_zap_report(json_data):
    """Return normalized High and Critical alerts from an OWASP ZAP JSON payload."""

    parsed_alerts = []

    for alert in _extract_alerts(json_data):
        risk = _normalize_risk(alert)
        if risk not in TARGET_RISKS:
            continue

        instances = [
            normalized
            for normalized in (_normalize_instance(instance) for instance in _as_list(alert.get("instances")))
            if normalized
        ]
        first_instance = instances[0] if instances else {}

        parsed = {
            "name": _first_present(alert.get("name"), alert.get("alert")),
            "alert": _first_present(alert.get("alert"), alert.get("name")),
            "risk": risk,
            "confidence": alert.get("confidence"),
            "url": _first_present(alert.get("url"), alert.get("uri"), first_instance.get("url")),
            "param": _first_present(alert.get("param"), first_instance.get("param")),
            "evidence": _first_present(alert.get("evidence"), first_instance.get("evidence")),
            "solution": alert.get("solution"),
            "reference": alert.get("reference"),
            "cweid": alert.get("cweid"),
            "wascid": alert.get("wascid"),
            "instances": instances,
        }

        parsed_alerts.append({key: value for key, value in parsed.items() if value not in (None, "")})

    return parsed_alerts
