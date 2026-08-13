from flask import Blueprint, request, jsonify
from database import query_db, execute_db
from auth import hash_password, verify_password, create_jwt_token, require_auth

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    phone = data.get("phone", "").strip()
    password = data.get("password", "")
    role = data.get("role", "customer").strip().lower()

    if not name or not email or not password or not phone:
        return jsonify({"error": "Name, email, phone, and password are required."}), 400

    if role not in ("customer", "provider"):
        return jsonify({"error": "Invalid role. Allowed roles: customer, provider."}), 400

    existing = query_db("SELECT id FROM users WHERE email = ?", (email,), one=True)
    if existing:
        return jsonify({"error": "An account with this email already exists."}), 409

    pw_hash = hash_password(password)
    user_id = execute_db(
        "INSERT INTO users (name, email, phone, password_hash, role) VALUES (?, ?, ?, ?, ?)",
        (name, email, phone, pw_hash, role)
    )

    provider_info = None
    if role == "provider":
        business_name = data.get("business_name", f"{name}'s Service").strip()
        description = data.get("description", "Professional service provider.").strip()
        experience_years = int(data.get("experience_years", 1))
        lat = float(data.get("latitude", 28.6139))
        lng = float(data.get("longitude", 77.2090))
        address = data.get("address_text", "City Center").strip()
        service_radius = float(data.get("service_radius_km", 10.0))
        pricing_note = data.get("pricing_note", "Standard service charges apply.").strip()
        starting_price = float(data.get("starting_price", 25.0))
        category_ids = data.get("category_ids", [])

        provider_id = execute_db(
            """INSERT INTO providers 
               (user_id, business_name, description, experience_years, latitude, longitude, address_text, 
                service_radius_km, availability_status, pricing_note, starting_price, verified, verification_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'available', ?, ?, 0, 'pending')""",
            (user_id, business_name, description, experience_years, lat, lng, address, service_radius, pricing_note, starting_price)
        )

        for cat_id in category_ids:
            execute_db(
                "INSERT INTO provider_categories (provider_id, category_id) VALUES (?, ?)",
                (provider_id, int(cat_id))
            )

        # Default operating hours (Mon-Sat 9 AM - 6 PM)
        for day in range(7):
            is_closed = 1 if day == 0 else 0
            execute_db(
                "INSERT INTO provider_hours (provider_id, day_of_week, open_time, close_time, is_closed) VALUES (?, ?, '09:00', '18:00', ?)",
                (provider_id, day, is_closed)
            )

        provider_info = {"id": provider_id, "business_name": business_name, "verified": False}

    token = create_jwt_token(user_id, role, email, name)

    return jsonify({
        "message": "Account created successfully.",
        "token": token,
        "user": {
            "id": user_id,
            "name": name,
            "email": email,
            "phone": phone,
            "role": role,
            "provider": provider_info
        }
    }), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = query_db("SELECT * FROM users WHERE email = ?", (email,), one=True)
    if not user or not verify_password(password, user["password_hash"]):
        return jsonify({"error": "Invalid email or password."}), 401

    provider_info = None
    if user["role"] == "provider":
        p = query_db("SELECT id, business_name, verified, verification_status, availability_status FROM providers WHERE user_id = ?", (user["id"],), one=True)
        if p:
            provider_info = dict(p)

    token = create_jwt_token(user["id"], user["role"], user["email"], user["name"])

    return jsonify({
        "message": "Login successful.",
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "phone": user["phone"],
            "role": user["role"],
            "provider": provider_info
        }
    }), 200

@auth_bp.route("/me", methods=["GET"])
@require_auth
def get_me():
    u = request.current_user
    user = query_db("SELECT id, name, email, phone, role, created_at FROM users WHERE id = ?", (u["sub"],), one=True)
    if not user:
        return jsonify({"error": "User not found."}), 404

    res = dict(user)
    if user["role"] == "provider":
        p = query_db("SELECT * FROM providers WHERE user_id = ?", (user["id"],), one=True)
        if p:
            res["provider"] = dict(p)

    return jsonify({"user": res}), 200
