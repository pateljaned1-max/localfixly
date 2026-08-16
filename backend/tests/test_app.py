import unittest
import os
import json
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.geo import haversine_distance
from auth import hash_password, verify_password, create_jwt_token, decode_jwt_token
from app import app
from database import init_db, query_db
from utils.seed import seed_database


class TestLocalFixBackend(unittest.TestCase):
    """Test suite for LocalFix backend API and utilities."""

    @classmethod
    def setUpClass(cls):
        """Set up test client and database for all tests."""
        os.environ["LOCALFIX_DB_PATH"] = ":memory:"
        init_db()  # Initialize database schema first
        seed_database()  # Then seed with test data
        cls.client = app.test_client()

    def setUp(self):
        """Reset app context before each test."""
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up after each test."""
        self.app_context.pop()

    def _decode_response(self, response):
        """Helper to decode Flask response data."""
        try:
            return json.loads(response.data.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            self.fail(f"Failed to decode response: {e}")

    # ============ UTILITY TESTS ============

    def test_haversine_distance(self):
        """Test haversine distance calculation between two coordinates."""
        # Distance between Connaught Place (28.6139, 77.2090)
        # and Barakhamba Road (28.6200, 77.2150) ~ 0.9 - 1.0 km
        dist = haversine_distance(28.6139, 77.2090, 28.6200, 77.2150)
        self.assertGreater(dist, 0.5, "Distance should be greater than 0.5 km")
        self.assertLess(dist, 2.0, "Distance should be less than 2.0 km")
        print(f"✓ Haversine distance: {dist:.2f} km")

    def test_password_hashing_and_verification(self):
        """Test password hashing and verification functions."""
        password = "Secret123!@#"

        # Test hashing
        hashed = hash_password(password)
        self.assertIsNotNone(hashed, "Hashed password should not be None")
        self.assertNotEqual(hashed, password, "Hashed password should differ from original")

        # Test correct password verification
        self.assertTrue(verify_password(password, hashed),
                        "Correct password should verify successfully")

        # Test incorrect password verification
        self.assertFalse(verify_password("WrongPassword", hashed),
                         "Wrong password should not verify")
        print("✓ Password hashing and verification working")

    def test_jwt_token_creation_and_decoding(self):
        """Test JWT token creation and decoding."""
        user_id = 10
        role = "provider"
        email = "test@provider.com"
        name = "Test Provider"

        # Create token
        token = create_jwt_token(user_id, role, email, name)
        self.assertIsNotNone(token, "Token should not be None")
        self.assertIsInstance(token, str, "Token should be a string")

        # Decode token
        payload = decode_jwt_token(token)
        self.assertIsNotNone(payload, "Payload should be decoded successfully")
        self.assertEqual(payload["user_id"], user_id, "User ID should match")
        self.assertEqual(payload["role"], role, "Role should match")
        self.assertEqual(payload["email"], email, "Email should match")
        self.assertEqual(payload["name"], name, "Name should match")
        print("✓ JWT token creation and decoding working")

    # ============ API ENDPOINT TESTS ============

    def test_categories_api_endpoint(self):
        """Test fetching categories from API."""
        res = self.client.get("/api/categories")
        self.assertEqual(res.status_code, 200, "Status code should be 200")

        data = self._decode_response(res)
        self.assertIn("categories", data, "Response should contain 'categories' key")
        self.assertIsInstance(data["categories"], list, "Categories should be a list")
        self.assertGreaterEqual(len(data["categories"]), 12,
                                "Should have at least 12 categories")
        print(f"✓ Categories API: Found {len(data['categories'])} categories")

    def test_role_enforcement_403_forbidden(self):
        """Test that customers cannot access admin routes."""
        # Create customer token
        token = create_jwt_token(99, "customer", "customer@test.com", "Cust Test")
        headers = {"Authorization": f"Bearer {token}"}

        # Customer accessing admin route
        res = self.client.get("/api/admin/stats", headers=headers)
        self.assertEqual(res.status_code, 403, "Should return 403 Forbidden")

        data = self._decode_response(res)
        self.assertIn("error", data, "Response should contain error message")
        self.assertIn("Forbidden", data["error"], "Error message should mention 'Forbidden'")
        print("✓ Role enforcement: 403 Forbidden working correctly")

    def test_missing_authorization_header(self):
        """Test that requests without auth token are rejected."""
        res = self.client.get("/api/admin/stats")
        self.assertIn(res.status_code, [401, 403],
                      "Should return 401 or 403 without auth header")
        print("✓ Missing auth header: Properly rejected")

    # ============ PROVIDER TESTS ============

    def test_provider_availability_toggle(self):
        """Test provider can toggle their availability status."""
        # Fetch seeded provider
        p_user = query_db("SELECT id, email FROM users WHERE role = 'provider' LIMIT 1;", one=True)
        self.assertIsNotNone(p_user, "Provider user should exist in seeded database")

        token = create_jwt_token(p_user["id"], "provider", p_user["email"], "Provider User")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Test setting availability to "busy"
        res = self.client.put(
            "/api/providers/availability",
            data=json.dumps({"availability_status": "busy"}),
            headers=headers
        )
        self.assertEqual(res.status_code, 200, "Status code should be 200")

        data = self._decode_response(res)
        self.assertEqual(data["availability_status"], "busy",
                         "Availability status should be updated to 'busy'")
        print("✓ Provider availability toggle: Working")

    # ============ BOOKING LIFECYCLE TESTS ============

    def test_booking_lifecycle_full_flow(self):
        """Test complete booking lifecycle: create -> accept."""
        # Fetch seeded users
        cust = query_db("SELECT id, email FROM users WHERE role = 'customer' LIMIT 1;", one=True)
        prov_u = query_db("SELECT id, email FROM users WHERE role = 'provider' LIMIT 1;", one=True)
        prov = query_db("SELECT id FROM providers WHERE user_id = ?",
                        (prov_u["id"],), one=True)
        cat = query_db("SELECT id FROM categories LIMIT 1;", one=True)

        self.assertIsNotNone(cust, "Customer should exist")
        self.assertIsNotNone(prov_u, "Provider user should exist")
        self.assertIsNotNone(prov, "Provider profile should exist")
        self.assertIsNotNone(cat, "Category should exist")

        cust_token = create_jwt_token(cust["id"], "customer", cust["email"], "Customer User")
        prov_token = create_jwt_token(prov_u["id"], "provider", prov_u["email"], "Provider User")

        # ===== STEP 1: Create booking =====
        booking_payload = {
            "provider_id": prov["id"],
            "category_id": cat["id"],
            "description": "Test leak issue",
            "address_text": "123 Test St, New Delhi",
            "preferred_date": "2026-08-20",
            "preferred_time": "10:00 AM"
        }

        res = self.client.post(
            "/api/bookings",
            data=json.dumps(booking_payload),
            headers={
                "Authorization": f"Bearer {cust_token}",
                "Content-Type": "application/json"
            }
        )
        self.assertEqual(res.status_code, 201, "Booking creation should return 201 Created")

        booking_data = self._decode_response(res)
        self.assertIn("booking_id", booking_data, "Response should contain booking_id")
        b_id = booking_data["booking_id"]
        print(f"✓ Booking created with ID: {b_id}")

        # ===== STEP 2: Provider accepts booking =====
        res = self.client.patch(
            f"/api/bookings/{b_id}/status",
            data=json.dumps({"status": "accepted"}),
            headers={
                "Authorization": f"Bearer {prov_token}",
                "Content-Type": "application/json"
            }
        )
        self.assertEqual(res.status_code, 200, "Status update should return 200")

        status_data = self._decode_response(res)
        self.assertEqual(status_data["new_status"], "accepted",
                         "Booking status should be 'accepted'")
        print("✓ Booking accepted by provider")

    def test_booking_creation_missing_fields(self):
        """Test that booking creation fails with missing required fields."""
        cust = query_db("SELECT id, email FROM users WHERE role = 'customer' LIMIT 1;", one=True)
        cust_token = create_jwt_token(cust["id"], "customer", cust["email"], "Customer User")

        # Missing required field: provider_id
        incomplete_payload = {
            "category_id": 1,
            "description": "Test",
            "address_text": "123 Test St"
        }

        res = self.client.post(
            "/api/bookings",
            data=json.dumps(incomplete_payload),
            headers={
                "Authorization": f"Bearer {cust_token}",
                "Content-Type": "application/json"
            }
        )
        self.assertIn(res.status_code, [400, 422],
                      "Should return 400 or 422 for missing fields")
        print("✓ Booking validation: Missing fields rejected")

    def test_customer_cannot_accept_own_booking(self):
        """Test that only provider can accept bookings."""
        cust = query_db("SELECT id, email FROM users WHERE role = 'customer' LIMIT 1;", one=True)
        prov = query_db("SELECT id FROM providers LIMIT 1;", one=True)
        cat = query_db("SELECT id FROM categories LIMIT 1;", one=True)

        cust_token = create_jwt_token(cust["id"], "customer", cust["email"], "Customer User")

        # Customer creates booking
        res = self.client.post(
            "/api/bookings",
            data=json.dumps({
                "provider_id": prov["id"],
                "category_id": cat["id"],
                "description": "Test",
                "address_text": "123 Test St",
                "preferred_date": "2026-08-20",
                "preferred_time": "10:00 AM"
            }),
            headers={
                "Authorization": f"Bearer {cust_token}",
                "Content-Type": "application/json"
            }
        )
        self.assertEqual(res.status_code, 201)
        b_id = self._decode_response(res)["booking_id"]

        # Customer tries to accept their own booking (should fail)
        res = self.client.patch(
            f"/api/bookings/{b_id}/status",
            data=json.dumps({"status": "accepted"}),
            headers={
                "Authorization": f"Bearer {cust_token}",
                "Content-Type": "application/json"
            }
        )
        self.assertIn(res.status_code, [403, 400],
                      "Customer should not be able to accept bookings")
        print("✓ Authorization: Customer cannot accept bookings")


if __name__ == "__main__":
    unittest.main(verbosity=2)