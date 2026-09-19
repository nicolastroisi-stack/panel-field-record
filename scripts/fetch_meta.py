#!/usr/bin/env python3
"""
Trae metricas de Meta Ads (ultimos 30 dias) usando el token de larga
duracion generado desde el Explorador de la API Graph.

Espera las variables de entorno:
  META_ACCESS_TOKEN
  META_AD_ACCOUNT_ID   (formato act_XXXXXXXXXX)
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

GRAPH_VERSION = "v21.0"
OUT_PATH = Path("data/meta_data.json")


def load_previous():
    """Si ya hay un data/meta_data.json de una corrida anterior, lo usamos
    como base para no perder el ultimo dato bueno si esta corrida falla."""
    if OUT_PATH.exists():
        try:
            return json.loads(OUT_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def write_result(result):
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps(result, indent=2, ensure_ascii=False))


def fetch():
    token = os.environ["META_ACCESS_TOKEN"]
    ad_account_id = os.environ["META_AD_ACCOUNT_ID"]

    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{ad_account_id}/insights"
    params = {
        "fields": "impressions,clicks,spend,reach,ctr,cpc,actions",
        "date_preset": "last_30d",
        "level": "account",
    }
    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.get(url, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    rows = payload.get("data", [])

    # Tambien traemos cuantas campanas estan activas ahora mismo.
    campaigns_url = f"https://graph.facebook.com/{GRAPH_VERSION}/{ad_account_id}/campaigns"
    campaigns_resp = requests.get(
        campaigns_url,
        params={"fields": "name,effective_status", "limit": 100},
        headers=headers,
        timeout=30,
    )
    campaigns_resp.raise_for_status()
    campaigns = campaigns_resp.json().get("data", [])
    active_campaigns = [c for c in campaigns if c.get("effective_status") == "ACTIVE"]

    if not rows:
        result = {
            "ok": True,
            "no_data": True,
            "active_campaigns": len(active_campaigns),
        }
    else:
        row = rows[0]
        result = {
            "ok": True,
            "no_data": False,
            "active_campaigns": len(active_campaigns),
            "impressions": int(row.get("impressions", 0)),
            "clicks": int(row.get("clicks", 0)),
            "spend": float(row.get("spend", 0)),
            "reach": int(row.get("reach", 0)),
            "ctr": float(row.get("ctr", 0)),
            "cpc": float(row.get("cpc", 0)) if row.get("cpc") else 0.0,
        }

    result["fetched_at"] = datetime.now(timezone.utc).isoformat()
    return result


def main():
    try:
        result = fetch()
        write_result(result)
    except Exception as exc:  # noqa: BLE001 - queremos capturar cualquier falla de red/API
        # No dejamos que un error de la API de Meta (token vencido, cuenta
        # bloqueada, rate limit, etc.) tire abajo todo el panel. Guardamos
        # el ultimo dato bueno que tengamos y marcamos el error, pero
        # salimos con codigo 0 para que el resto del workflow siga.
        print(f"[error] fetch_meta.py fallo: {exc}", file=sys.stderr)
        previous = load_previous()
        previous["ok"] = False
        previous["error"] = str(exc)
        previous["error_at"] = datetime.now(timezone.utc).isoformat()
        # Si nunca hubo una corrida buena antes, dejamos no_data en True
        # para que el panel muestre el mensaje de "todavia sin datos".
        previous.setdefault("no_data", True)
        write_result(previous)


if __name__ == "__main__":
    main()
