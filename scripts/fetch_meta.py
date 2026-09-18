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
from pathlib import Path

import requests

GRAPH_VERSION = "v21.0"


def main():
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

    out_path = Path("data/meta_data.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
