# Webhook ZAP Serverless

## Objective

Automate the ingestion of OWASP ZAP JSON reports, filter `High` and `Critical` risk alerts, and notify the team through a configurable HTTP webhook. The flow is designed for automated nightly penetration testing and immediate prioritization of critical findings.

## Architecture (Vercel)

```text
OWASP ZAP API -> Vercel Serverless Function (/api/index.py) -> Parser -> Notifier -> Team
```

The Python endpoint in `api/index.py` uses `BaseHTTPRequestHandler` to receive `POST` requests. The JSON body is forwarded to `parse_zap_report`, which normalizes and filters severe alerts. The resulting list is sent to `dispatch_alert`, which builds a generic JSON payload with visual blocks and publishes it to the environment-defined destination.

## Environment Variables

| Key | Purpose |
| --- | --- |
| `TEAM_WEBHOOK_URL` | HTTP URL that receives the team's consolidated notification. |
| `ZAP_API_KEY` | Optional key used to authenticate calls through `X-ZAP-API-Key` or `Authorization: Bearer`. |

## Routes

| Method | Route | Description |
| --- | --- | --- |
| `POST` | `/api` | Receives the OWASP ZAP report and dispatches notifications for `High` and `Critical` alerts. |

## Core Files

| File | Responsibility |
| --- | --- |
| `api/index.py` | HTTP Serverless handler on Vercel. |
| `api/parser.py` | Extraction and normalization of severe OWASP ZAP alerts. |
| `api/notifier.py` | Formatting and dispatch of the payload to the team webhook. |
| `vercel.json` | Rewrites from `/api` and `/api/*` to `api/index.py`. |
