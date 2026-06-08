# Webhook ZAP Serverless

## Objectif

Automatiser la reception des rapports JSON OWASP ZAP, filtrer les alertes de risque `High` et `Critical`, puis notifier l'equipe au moyen d'un webhook HTTP configurable. Le flux est concu pour des tests d'intrusion nocturnes automatises et pour la priorisation immediate des constats critiques.

## Architecture (Vercel)

```text
OWASP ZAP API -> Vercel Serverless Function (/api/index.py) -> Parser -> Notifier -> Equipe
```

Le point d'entree Python dans `api/index.py` utilise `BaseHTTPRequestHandler` pour recevoir les requetes `POST`. Le corps JSON est transmis a `parse_zap_report`, qui normalise et filtre les alertes severes. La liste obtenue est envoyee a `dispatch_alert`, qui construit une charge utile JSON generique avec des blocs visuels et la publie vers la destination definie par l'environnement.

## Variables d'Environnement

| Cle | Usage |
| --- | --- |
| `TEAM_WEBHOOK_URL` | URL HTTP recevant la notification consolidee de l'equipe. |
| `ZAP_API_KEY` | Cle optionnelle pour authentifier les appels via `X-ZAP-API-Key` ou `Authorization: Bearer`. |

## Routes

| Methode | Route | Description |
| --- | --- | --- |
| `POST` | `/api` | Recoit le rapport OWASP ZAP et declenche les notifications pour les alertes `High` et `Critical`. |

## Fichiers Principaux

| Fichier | Responsabilite |
| --- | --- |
| `api/index.py` | Handler HTTP Serverless sur Vercel. |
| `api/parser.py` | Extraction et normalisation des alertes OWASP ZAP severes. |
| `api/notifier.py` | Formatage et expedition de la charge utile vers le webhook de l'equipe. |
| `vercel.json` | Rewrites de `/api` et `/api/*` vers `api/index.py`. |
