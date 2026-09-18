#!/usr/bin/env python3
"""
Trae metricas de trafico (ultimos 28 dias) desde Google Analytics (GA4)
usando la cuenta de servicio que ya tiene permiso "Lector" sobre la propiedad.

Espera la variable de entorno GA_CRED_PATH apuntando a un archivo con el
JSON de la cuenta de servicio (el workflow de GitHub Actions lo escribe
ahi a partir del secret GA_SERVICE_ACCOUNT_JSON).
"""
import json
import os
import sys
from pathlib import Path

from google.oauth2 import service_account
from google.analytics.admin_v1beta import AnalyticsAdminServiceClient
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, RunReportRequest

SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
SITE_HINT = "fieldrecord"


def get_credentials():
    cred_path = os.environ.get("GA_CRED_PATH")
    if not cred_path or not Path(cred_path).exists():
        raise RuntimeError("GA_CRED_PATH no esta seteado o el archivo no existe.")
    return service_account.Credentials.from_service_account_file(cred_path, scopes=SCOPES)


def find_property(admin_client):
    summaries = list(admin_client.list_account_summaries())
    candidates = [p for acc in summaries for p in acc.property_summaries]
    if not candidates:
        raise RuntimeError("La cuenta de servicio no ve ninguna propiedad de GA4.")
    if len(candidates) == 1:
        return candidates[0]
    for prop in candidates:
        if SITE_HINT.lower() in prop.display_name.lower():
            return prop
    print(f"[aviso] {len(candidates)} propiedades visibles, ninguna matchea '{SITE_HINT}'. Usando la primera.", file=sys.stderr)
    return candidates[0]


def main():
    creds = get_credentials()
    admin_client = AnalyticsAdminServiceClient(credentials=creds)
    data_client = BetaAnalyticsDataClient(credentials=creds)

    prop = find_property(admin_client)
    property_id = prop.property.split("/")[-1]

    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date="28daysAgo", end_date="today")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="activeUsers"),
            Metric(name="newUsers"),
            Metric(name="averageSessionDuration"),
            Metric(name="engagementRate"),
        ],
    )
    response = data_client.run_report(request)

    if not response.rows:
        result = {"ok": True, "property_name": prop.display_name, "no_data": True}
    else:
        row = response.rows[0]
        sessions, active_users, new_users, avg_duration, engagement_rate = [v.value for v in row.metric_values]
        pct_new = round(float(new_users) / float(active_users) * 100, 1) if float(active_users) else 0.0
        mins, secs = divmod(int(float(avg_duration)), 60)
        result = {
            "ok": True,
            "no_data": False,
            "property_name": prop.display_name,
            "sessions_28d": int(float(sessions)),
            "active_users_28d": int(float(active_users)),
            "new_users_28d": int(float(new_users)),
            "pct_new_users": pct_new,
            "avg_session_duration_fmt": f"{mins}:{secs:02d}",
            "engagement_rate_pct": round(float(engagement_rate) * 100, 1),
        }

    out_path = Path("data/ga_data.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
