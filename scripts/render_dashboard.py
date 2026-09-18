#!/usr/bin/env python3
"""
Junta data/ga_data.json + data/meta_data.json y arma docs/index.html
a partir de template/dashboard_template.html, reemplazando los
placeholders {{...}}.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = ROOT / "template" / "dashboard_template.html"
OUT_PATH = ROOT / "docs" / "index.html"


def load_json(path, default=None):
    p = Path(path)
    if not p.exists():
        return default or {}
    return json.loads(p.read_text())


def main():
    ga = load_json("data/ga_data.json")
    meta = load_json("data/meta_data.json")

    updated_at = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

    if ga.get("no_data"):
        ga_vals = dict(
            GA_ACTIVE_USERS="0", GA_NEW_USERS="0", GA_PCT_NEW="0",
            GA_ENGAGEMENT="—",
            GA_NOTE="Google Analytics conectado, pero todavia sin trafico registrado en los ultimos 28 dias.",
        )
    else:
        ga_vals = dict(
            GA_ACTIVE_USERS=str(ga.get("active_users_28d", "—")),
            GA_NEW_USERS=str(ga.get("new_users_28d", "—")),
            GA_PCT_NEW=str(ga.get("pct_new_users", "—")),
            GA_ENGAGEMENT=ga.get("avg_session_duration_fmt", "—"),
            GA_NOTE="Datos automaticos de Google Analytics (ultimos 28 dias).",
        )

    if meta.get("no_data") or not meta:
        meta_vals = dict(
            META_ACTIVE_CAMPAIGNS=str(meta.get("active_campaigns", "—")),
            META_SPEND="0.00", META_IMPRESSIONS="0", META_CLICKS="0",
            META_NOTE="Meta Ads conectado, pero las campanas activas todavia no generaron impresiones ni gasto en los ultimos 30 dias.",
        )
    else:
        meta_vals = dict(
            META_ACTIVE_CAMPAIGNS=str(meta.get("active_campaigns", "—")),
            META_SPEND=f"{meta.get('spend', 0):.2f}",
            META_IMPRESSIONS=str(meta.get("impressions", 0)),
            META_CLICKS=str(meta.get("clicks", 0)),
            META_NOTE="Datos automaticos de Meta Ads (ultimos 30 dias).",
        )

    replacements = {"UPDATED_AT": updated_at, **ga_vals, **meta_vals}

    html = TEMPLATE_PATH.read_text(encoding="utf-8")
    for key, value in replacements.items():
        html = html.replace("{{" + key + "}}", str(value))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"Escrito {OUT_PATH} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
