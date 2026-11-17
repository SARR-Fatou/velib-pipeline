"""Orchestration du pipeline ETL Vélib'.

Lancement :  python -m src.run_pipeline
Sorties    :  data/history.csv            (historique, versionné)
              docs/data/latest.json       (état actuel, lu par le tableau de bord)
              docs/data/history.json      (série temporelle + profil horaire)
"""
import json
import os
import sys
from datetime import datetime, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python < 3.9
    ZoneInfo = None

from src.extract import extract
from src.transform import transform
from src import load

ROOT = load.ROOT
DATA_DIR = os.path.join(ROOT, "data")
DOCS_DATA = os.path.join(ROOT, "docs", "data")
HISTORY_CSV = os.path.join(DATA_DIR, "history.csv")
DB_PATH = os.path.join(DATA_DIR, "velib.sqlite")
HISTORY_POINTS = 24 * 14  # 14 jours affichés sur le graphique


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(DOCS_DATA, exist_ok=True)

    # 1. Extract
    information, status, source_ts = extract()
    print(f"[extract]   {len(information)} stations (référentiel), {len(status)} états")

    # 2. Transform
    stations, quality = transform(information, status)
    print(f"[transform] {quality}")
    if len(stations) < 500:
        sys.exit("Moins de 500 stations valides : données suspectes, arrêt du pipeline.")

    # 3. Load
    now_utc = datetime.fromtimestamp(source_ts, tz=timezone.utc) if source_ts else datetime.now(timezone.utc)
    now_utc = now_utc.replace(minute=0, second=0, microsecond=0)  # une ligne par heure
    local = now_utc.astimezone(ZoneInfo("Europe/Paris")) if ZoneInfo else now_utc
    snapshot = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    con = load.connect(DB_PATH)
    load.load_snapshot(con, stations)
    load.load_history(con, HISTORY_CSV)

    kpis = load.run_queries(con)
    already = con.execute("SELECT 1 FROM network_history WHERE snapshot_utc = ?", (snapshot,)).fetchone()
    if not already:
        load.append_history(con, HISTORY_CSV, snapshot, local.hour, local.weekday(), kpis["network_now"][0])
        kpis["hourly_profile"] = load.run_queries(con, ["hourly_profile"])["hourly_profile"]
    con.commit()
    print(f"[load]      {kpis['network_now'][0]}")

    # 4. Export pour le tableau de bord
    latest = {
        "updated_at": now_utc.isoformat(),
        "network": kpis["network_now"][0],
        "quality": quality,
        "fill_distribution": kpis["fill_distribution"],
        "biggest_empty": kpis["biggest_empty"],
        "most_ebikes": kpis["most_ebikes"],
        # Coordonnées arrondies + données compactes pour la carte
        "stations": [
            [s["name"], round(s["lat"], 5), round(s["lon"], 5), s["capacity"], s["mechanical"], s["ebike"], s["docks"]]
            for s in stations
        ],
    }
    rows = con.execute(
        "SELECT snapshot_utc, bikes, mechanical, ebike, empty_stations, full_stations "
        "FROM network_history ORDER BY snapshot_utc DESC LIMIT ?", (HISTORY_POINTS,)
    ).fetchall()
    history = {
        "series": [dict(r) for r in reversed(rows)],
        "hourly_profile": kpis["hourly_profile"],
        "total_snapshots": con.execute("SELECT COUNT(*) FROM network_history").fetchone()[0],
    }
    con.close()

    with open(os.path.join(DOCS_DATA, "latest.json"), "w", encoding="utf-8") as f:
        json.dump(latest, f, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(DOCS_DATA, "history.json"), "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, separators=(",", ":"))
    print("[export]    docs/data/latest.json, docs/data/history.json")


if __name__ == "__main__":
    main()
