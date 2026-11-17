"""Étape 3 — LOAD : chargement en base SQLite, historisation et calcul des KPI en SQL."""
import csv
import os
import re
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL_DIR = os.path.join(ROOT, "sql")
HISTORY_COLUMNS = [
    "snapshot_utc", "local_hour", "weekday", "stations", "bikes", "mechanical",
    "ebike", "docks", "empty_stations", "full_stations",
]


def read_named_queries(path):
    """Lit un fichier .sql où chaque requête commence par `-- name: <nom>`."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    parts = re.split(r"^-- name:\s*(\w+)\s*$", text, flags=re.MULTILINE)
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}


def connect(db_path):
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    with open(os.path.join(SQL_DIR, "schema.sql"), encoding="utf-8") as f:
        con.executescript(f.read())
    return con


def load_snapshot(con, stations):
    con.executemany(
        "INSERT INTO station (station_id, code, name, lat, lon, capacity) "
        "VALUES (:station_id, :code, :name, :lat, :lon, :capacity)",
        stations,
    )
    con.executemany(
        "INSERT INTO station_status (station_id, bikes, mechanical, ebike, docks, "
        "is_renting, is_returning, last_reported) VALUES (:station_id, :bikes, "
        ":mechanical, :ebike, :docks, :is_renting, :is_returning, :last_reported)",
        stations,
    )


def load_history(con, history_csv):
    """Recharge l'historique (CSV versionné dans Git) dans la table network_history."""
    if not os.path.exists(history_csv):
        return
    with open(history_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    con.executemany(
        f"INSERT OR REPLACE INTO network_history ({', '.join(HISTORY_COLUMNS)}) "
        f"VALUES ({', '.join(':' + c for c in HISTORY_COLUMNS)})",
        rows,
    )


def append_history(con, history_csv, snapshot_utc, local_hour, weekday, now):
    row = {
        "snapshot_utc": snapshot_utc, "local_hour": local_hour, "weekday": weekday,
        "stations": now["stations"], "bikes": now["bikes"], "mechanical": now["mechanical"],
        "ebike": now["ebike"], "docks": now["docks"],
        "empty_stations": now["empty_stations"], "full_stations": now["full_stations"],
    }
    con.execute(
        f"INSERT OR REPLACE INTO network_history ({', '.join(HISTORY_COLUMNS)}) "
        f"VALUES ({', '.join(':' + c for c in HISTORY_COLUMNS)})",
        row,
    )
    new_file = not os.path.exists(history_csv)
    with open(history_csv, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HISTORY_COLUMNS)
        if new_file:
            writer.writeheader()
        writer.writerow(row)


def run_queries(con, names=None):
    queries = read_named_queries(os.path.join(SQL_DIR, "kpis.sql"))
    results = {}
    for name, sql in queries.items():
        if names and name not in names:
            continue
        results[name] = [dict(r) for r in con.execute(sql).fetchall()]
    return results
