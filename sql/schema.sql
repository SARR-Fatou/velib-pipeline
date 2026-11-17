-- Modèle de données (SQLite)
-- station        : référentiel des stations (une ligne par station)
-- station_status : état de chaque station au moment de la collecte
-- network_history: indicateurs agrégés du réseau, une ligne par collecte

DROP TABLE IF EXISTS station_status;
DROP TABLE IF EXISTS station;
DROP TABLE IF EXISTS network_history;

CREATE TABLE station (
    station_id  INTEGER PRIMARY KEY,
    code        TEXT NOT NULL,
    name        TEXT NOT NULL,
    lat         REAL NOT NULL,
    lon         REAL NOT NULL,
    capacity    INTEGER NOT NULL CHECK (capacity >= 0)
);

CREATE TABLE station_status (
    station_id    INTEGER PRIMARY KEY REFERENCES station(station_id),
    bikes         INTEGER NOT NULL CHECK (bikes >= 0),
    mechanical    INTEGER NOT NULL CHECK (mechanical >= 0),
    ebike         INTEGER NOT NULL CHECK (ebike >= 0),
    docks         INTEGER NOT NULL CHECK (docks >= 0),
    is_renting    INTEGER NOT NULL,
    is_returning  INTEGER NOT NULL,
    last_reported INTEGER NOT NULL
);

CREATE TABLE network_history (
    snapshot_utc    TEXT PRIMARY KEY,   -- ISO 8601
    local_hour      INTEGER NOT NULL,   -- heure de Paris (0-23)
    weekday         INTEGER NOT NULL,   -- 0 = lundi
    stations        INTEGER NOT NULL,
    bikes           INTEGER NOT NULL,
    mechanical      INTEGER NOT NULL,
    ebike           INTEGER NOT NULL,
    docks           INTEGER NOT NULL,
    empty_stations  INTEGER NOT NULL,
    full_stations   INTEGER NOT NULL
);
