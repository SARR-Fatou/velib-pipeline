"""Tests unitaires de l'étape de transformation.  Lancement : python -m unittest"""
import unittest

from src.transform import transform

INFO = [
    {"station_id": 1, "stationCode": "1001", "name": " Gare ", "lat": 48.8, "lon": 2.3, "capacity": 20},
    {"station_id": 2, "stationCode": "1002", "name": "Place", "lat": 48.9, "lon": 2.4, "capacity": 10},
    {"station_id": 2, "stationCode": "1002", "name": "Place (doublon)", "lat": 48.9, "lon": 2.4, "capacity": 10},
]


def status(sid, mech, ebike, docks, installed=1):
    return {
        "station_id": sid, "num_bikes_available": mech + ebike,
        "num_bikes_available_types": [{"mechanical": mech}, {"ebike": ebike}],
        "num_docks_available": docks, "is_installed": installed,
        "is_renting": 1, "is_returning": 1, "last_reported": 0,
    }


class TransformTest(unittest.TestCase):
    def test_join_and_bike_types(self):
        clean, q = transform(INFO, [status(1, 3, 2, 15)])
        self.assertEqual(len(clean), 1)
        s = clean[0]
        self.assertEqual((s["name"], s["bikes"], s["mechanical"], s["ebike"]), ("Gare", 5, 3, 2))
        self.assertEqual(q["doublons"], 1)

    def test_rejects_unknown_and_uninstalled(self):
        clean, q = transform(INFO, [status(99, 1, 1, 1), status(2, 1, 0, 9, installed=0)])
        self.assertEqual(clean, [])
        self.assertEqual(q["sans_information"], 1)
        self.assertEqual(q["non_installees"], 1)

    def test_rejects_negative_values(self):
        clean, q = transform(INFO, [status(1, -1, 0, 5)])
        self.assertEqual(clean, [])
        self.assertEqual(q["valeurs_negatives"], 1)

    def test_flags_over_capacity(self):
        clean, q = transform(INFO, [status(2, 8, 2, 5)])
        self.assertEqual(len(clean), 1)
        self.assertEqual(q["depassement_capacite"], 1)


if __name__ == "__main__":
    unittest.main()
