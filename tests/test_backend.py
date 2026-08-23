import unittest

from backend.app import app, parse_world_id


class BackendTests(unittest.TestCase):
    def test_world_ids(self):
        self.assertEqual(parse_world_id("001"), ("001", "real", "001"))
        self.assertEqual(parse_world_id("fantasia:003"), ("fantasia:003", "fantasia", "003"))

    def test_health_route_exists(self):
        client = app.test_client()
        response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)


if __name__ == "__main__":
    unittest.main()
