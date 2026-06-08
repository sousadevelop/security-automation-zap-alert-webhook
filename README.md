# Webhook ZAP Serverless

## Objetivo

Automatizar o recebimento de relatorios JSON do OWASP ZAP, filtrar alertas de risco `High` e `Critical`, e notificar a equipe por meio de um webhook HTTP configuravel. O fluxo foi desenhado para execucoes de pentest noturno automatizado e priorizacao imediata de achados criticos.

## Arquitetura (Vercel)

```text
OWASP ZAP API -> Vercel Serverless Function (/api/index.py) -> Parser -> Notifier -> Equipe
```

O endpoint Python em `api/index.py` usa `BaseHTTPRequestHandler` para receber requisicoes `POST`. O corpo JSON e encaminhado para `parse_zap_report`, que normaliza e filtra alertas severos. A lista resultante e enviada para `dispatch_alert`, que monta um payload JSON generico com blocos visuais e publica no destino definido por ambiente.

## Variaveis de Ambiente

| Chave | Uso |
| --- | --- |
| `TEAM_WEBHOOK_URL` | URL HTTP que recebera a notificacao consolidada da equipe. |
| `ZAP_API_KEY` | Chave opcional para autenticar chamadas via `X-ZAP-API-Key` ou `Authorization: Bearer`. |

## Rotas

| Metodo | Rota | Descricao |
| --- | --- | --- |
| `POST` | `/api` | Recebe o relatorio OWASP ZAP e dispara notificacoes para alertas `High` e `Critical`. |

## Arquivos Principais

| Arquivo | Responsabilidade |
| --- | --- |
| `api/index.py` | Handler Serverless HTTP no Vercel. |
| `api/parser.py` | Extracao e normalizacao de alertas OWASP ZAP severos. |
| `api/notifier.py` | Formatacao e despacho do payload para o webhook da equipe. |
| `vercel.json` | Rewrites de `/api` e `/api/*` para `api/index.py`. |
