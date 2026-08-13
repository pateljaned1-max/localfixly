import unittest
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.geo import haversine_distance
from auth import hash_password, verify_password, create_jwt_token, decode_jwt_token
from app import app
from database import init_db
from utils.seed import seed_database

class TestLocalFixBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["LOCALFIX_DB_PATH"] = ":memory:"
        seed_database()
        cls.client = app.test_client()

    def test_haversine_distance(self):
        # Distance between Connaught Place (28.6139, 77.2090) and Barakhamba Road (28.6200, 77.2150) ~ 0.9 - 1.0 km
        dist = haversine_distance(28.6139, 77.2090, 28.6200, 77.2150)
        self.assertGreater(dist, 0.5)
        self.assertLess(dist, 2.0)

    def test_password_and_jwt(self):
        hashed = hash_password("Secret123")
        self.assertTrue(verify_password("Secret123", hashed))
        self.assertFalse(verify_password("WrongPassword", hashed))

        token = create_jwt_token(10, "provider", "test@provider.com", "Test Provider")
        payload = decode_jwt_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["role"], "provider")
        self.assertEqual(payload["email"], "test@provider.com")

    def test_categories_api(self):
        res = self.client.get("/api/categories")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("categories", data)
        self.assertGreaterEqual(len(data["categories"]), 12)

    def test_role_enforcement_403(self):
        # Create customer token
        token = create_jwt_token(99, "customer", "customer@test.com", "Cust Test")
        headers = {"Authorization": f"Bearer {token}"}

        # Customer accessing admin route -> MUST receive 403 Forbidden
        res = self.client.get("/api/admin/stats", headers=headers)
        self.assertEqual(res.status_code, 403)
        data = json.loads(res.data)
        self.assertIn("Forbidden", data["error"])

    def test_provider_availability_toggle(self):
        # Fetch actual seeded provider user_id
        from database import query_db
        p_user = query_db("SELECT id, email FROM users WHERE role = 'provider' LIMIT 1;", one=True)
        token = create_jwt_token(p_user["id"], "provider", p_user["email"], "Provider User")
        headers = {"Authorization": f"Bearer {token}"}

        res = self.client.put("/api/providers/availability", 
                              data=json.dumps({"availability_status": "busy"}),
                              content_type="application/json",
                              headers=headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["availability_status"], "busy")

    def test_booking_lifecycle(self):
        from database import query_db
        cust = query_db("SELECT id, email FROM users WHERE role = 'customer' LIMIT 1;", one=True)
        prov_u = query_db("SELECT id, email FROM users WHERE role = 'provider' LIMIT 1;", one=True)
        prov = query_db("SELECT id FROM providers WHERE user_id = ?", (prov_u["id"],), one=True)
        cat = query_db("SELECT id FROM categories LIMIT 1;", one=True)

        cust_token = create_jwt_token(cust["id"], "customer", cust["email"], "Customer User")
        prov_token = create_jwt_token(prov_u["id"], "provider", prov_u["email"], "Provider User")

        # 1. Create booking
        res = self.client.post("/api/bookings",
                               data=json.dumps({
                                   "provider_id": prov["id"],
                                   "category_id": cat["id"],
                                   "description": "Test leak issue",
                                   "address_text": "123 Test St",
                                   "preferred_date": "2026-08-15",
                                   "preferred_time": "10:00 AM"
                               }),
                               content_type="application/json",
                               headers={"Authorization": f"Bearer {cust_token}"})
        self.assertEqual(res.status_code, 201)
        b_id = json.loads(res.data)["booking_id"]

        # 2. Provider Accepts
        res = self.client.patch(f"/api/bookings/{b_id}/status",
                                data=json.dumps({"status": "accepted"}),
                                content_type="application/json",
                                headers={"Authorization": f"Bearer {prov_token}"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json.loads(res.data)["new_status"], "accepted")

if __name__ == "__main__":
    unittest.main()
