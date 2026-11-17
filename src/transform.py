"""Étape 2 — TRANSFORM : nettoyage, jointure et contrôles qualité.

On joint les deux flux sur `station_id`, on sépare les vélos mécaniques et
électriques, et on écarte les lignes incohérentes (station non installée,
compteurs négatifs, total supérieur à la capacité...).
"""


def _bike_types(status_row):
    """Le flux donne une liste du type [{"mechanical": 4}, {"ebike": 5}]."""
    mech = ebike = 0
    for item in status_row.get("num_bikes_available_types") or []:
        mech += int(item.get("mechanical", 0) or 0)
        ebike += int(item.get("ebike", 0) or 0)
    return mech, ebike


def transform(information, status):
    """Retourne (stations_propres, rapport_qualite)."""
    info_by_id = {}
    duplicates = 0
    for row in information:
        sid = row.get("station_id")
        if sid in info_by_id:
            duplicates += 1
            continue
        info_by_id[sid] = row

    clean, issues = [], {
        "doublons": duplicates,
        "sans_information": 0,
        "non_installees": 0,
        "valeurs_negatives": 0,
        "depassement_capacite": 0,
    }

    for st in status:
        sid = st.get("station_id")
        info = info_by_id.get(sid)
        if info is None:
            issues["sans_information"] += 1
            continue
        if not st.get("is_installed"):
            issues["non_installees"] += 1
            continue

        mech, ebike = _bike_types(st)
        bikes = int(st.get("num_bikes_available", mech + ebike) or 0)
        docks = int(st.get("num_docks_available", 0) or 0)
        capacity = int(info.get("capacity") or 0)

        if min(bikes, docks, mech, ebike, capacity) < 0:
            issues["valeurs_negatives"] += 1
            continue
        if capacity and bikes + docks > capacity:
            # Cas réel : bornes en maintenance comptées différemment. On garde
            # la station mais on la signale.
            issues["depassement_capacite"] += 1

        clean.append({
            "station_id": sid,
            "code": str(info.get("stationCode") or st.get("stationCode") or ""),
            "name": (info.get("name") or "").strip(),
            "lat": float(info.get("lat")),
            "lon": float(info.get("lon")),
            "capacity": capacity,
            "bikes": bikes,
            "mechanical": mech,
            "ebike": ebike,
            "docks": docks,
            "is_renting": int(bool(st.get("is_renting"))),
            "is_returning": int(bool(st.get("is_returning"))),
            "last_reported": int(st.get("last_reported") or 0),
        })

    issues["stations_retenues"] = len(clean)
    return clean, issues
