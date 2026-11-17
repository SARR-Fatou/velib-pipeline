-- Indicateurs calculés en SQL à chaque collecte.
-- Chaque requête est précédée d'un commentaire "-- name: <nom>" lu par load.py.

-- name: network_now
-- Indicateurs globaux du réseau à l'instant T
SELECT
    COUNT(*)                                             AS stations,
    SUM(s.bikes)                                         AS bikes,
    SUM(s.mechanical)                                    AS mechanical,
    SUM(s.ebike)                                         AS ebike,
    SUM(s.docks)                                         AS docks,
    SUM(st.capacity)                                     AS capacity,
    SUM(CASE WHEN s.bikes = 0 THEN 1 ELSE 0 END)         AS empty_stations,
    SUM(CASE WHEN s.docks = 0 THEN 1 ELSE 0 END)         AS full_stations,
    ROUND(100.0 * SUM(s.ebike) / NULLIF(SUM(s.bikes), 0), 1) AS ebike_share_pct,
    ROUND(100.0 * SUM(s.bikes) / NULLIF(SUM(st.capacity), 0), 1) AS fill_rate_pct
FROM station_status s
JOIN station st USING (station_id);

-- name: fill_distribution
-- Répartition des stations selon leur taux de remplissage
WITH classified AS (
    SELECT
        CASE
            WHEN s.bikes = 0                          THEN 0
            WHEN s.docks = 0                          THEN 5
            WHEN 1.0 * s.bikes / st.capacity < 0.25   THEN 1
            WHEN 1.0 * s.bikes / st.capacity < 0.50   THEN 2
            WHEN 1.0 * s.bikes / st.capacity < 0.75   THEN 3
            ELSE 4
        END AS bucket_order
    FROM station_status s
    JOIN station st USING (station_id)
    WHERE st.capacity > 0
)
SELECT
    CASE bucket_order
        WHEN 0 THEN 'Vide'
        WHEN 1 THEN '1-24 %'
        WHEN 2 THEN '25-49 %'
        WHEN 3 THEN '50-74 %'
        WHEN 4 THEN '75-99 %'
        ELSE 'Pleine'
    END AS bucket,
    COUNT(*) AS stations
FROM classified
GROUP BY bucket_order
ORDER BY bucket_order;

-- name: biggest_empty
-- Les plus grandes stations actuellement sans aucun vélo
SELECT st.name, st.capacity, s.docks
FROM station_status s
JOIN station st USING (station_id)
WHERE s.bikes = 0 AND s.is_renting = 1
ORDER BY st.capacity DESC, st.name
LIMIT 10;

-- name: most_ebikes
-- Stations avec le plus de vélos électriques disponibles
SELECT st.name, s.ebike, s.bikes
FROM station_status s
JOIN station st USING (station_id)
ORDER BY s.ebike DESC, s.bikes DESC
LIMIT 10;

-- name: hourly_profile
-- Profil moyen par heure de la journée, calculé sur tout l'historique
SELECT
    local_hour,
    ROUND(AVG(bikes))          AS avg_bikes,
    ROUND(AVG(ebike))          AS avg_ebike,
    ROUND(AVG(empty_stations)) AS avg_empty,
    COUNT(*)                   AS samples
FROM network_history
GROUP BY local_hour
ORDER BY local_hour;
