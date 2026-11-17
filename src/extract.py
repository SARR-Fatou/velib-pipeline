"""Étape 1 — EXTRACT : récupération des données ouvertes Vélib' Métropole (format GBFS).

Deux flux sont publiés par l'opérateur :
  - station_information.json : données "statiques" (nom, position GPS, capacité)
  - station_status.json      : données "dynamiques" (vélos et bornes disponibles)
"""
import json
import time
import urllib.request

BASE_URL = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole"
FEEDS = {
    "information": f"{BASE_URL}/station_information.json",
    "status": f"{BASE_URL}/station_status.json",
}


def fetch_json(url, retries=3, timeout=30):
    """Télécharge un JSON, avec quelques tentatives en cas d'erreur réseau."""
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "velib-pipeline (projet etudiant)"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.load(resp)
        except Exception as exc:  # réseau, JSON invalide...
            last_error = exc
            time.sleep(2 * attempt)
    raise RuntimeError(f"Impossible de récupérer {url} : {last_error}")


def extract():
    """Retourne (stations_information, stations_status, horodatage_source)."""
    info = fetch_json(FEEDS["information"])
    status = fetch_json(FEEDS["status"])
    source_ts = status.get("lastUpdatedOther") or status.get("last_updated")
    return info["data"]["stations"], status["data"]["stations"], source_ts
