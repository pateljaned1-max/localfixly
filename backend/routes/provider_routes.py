from flask import Blueprint, request, jsonify
from database import query_db, execute_db
from utils.geo import haversine_distance
from auth import require_auth, require_role
import datetime

provider_bp = Blueprint("providers", __name__)

@provider_bp.route("/search", methods=["GET"])
def search_providers():
    # Query parameters
    category_id = request.args.get("category_id", type=int)
    category_slug = request.args.get("category", type=str)
    user_lat = request.args.get("lat", type=float, default=28.6139)
    user_lng = request.args.get("lng", type=float, default=77.2090)
    radius_km = request.args.get("radius", type=float, default=10.0)
    available_now = request.args.get("available_now", type=str) # 'true' / 'false'
    availability = request.args.get("availability", type=str) # 'available', 'busy', 'offline'
    min_rating = request.args.get("min_rating", type=float, default=0.0)
    verified_only = request.args.get("verified_only", type=str) # 'true'
    min_experience = request.args.get("min_experience", type=int, default=0)
    max_price = request.args.get("max_price", type=float)
    sort_by = request.args.get("sort_by", type=str, default="availability") # availability, distance, rating, price

    # Build SQL query for providers
    query = """
        SELECT p.*, u.name as provider_user_name, u.phone as provider_phone, u.email as provider_email
        FROM providers p
        JOIN users u ON u.id = p.user_id
    """
    params = []
    where_clauses = ["u.role = 'provider'"]

    if category_slug:
        cat = query_db("SELECT id FROM categories WHERE slug = ?;", (category_slug,), one=True)
        if cat:
            category_id = cat["id"]

    if category_id:
        query += " JOIN provider_categories pc ON pc.provider_id = p.id"
        where_clauses.append("pc.category_id = ?")
        params.append(category_id)

    if available_now == "true":
        where_clauses.append("p.availability_status = 'available'")
    elif availability:
        where_clauses.append("p.availability_status = ?")
        params.append(availability)

    if verified_only == "true":
        where_clauses.append("p.verified = 1")

    if min_rating > 0:
        where_clauses.append("p.avg_rating >= ?")
        params.append(min_rating)

    if min_experience > 0:
        where_clauses.append("p.experience_years >= ?")
        params.append(min_experience)

    if max_price is not None:
        where_clauses.append("p.starting_price <= ?")
        params.append(max_price)

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " GROUP BY p.id"

    providers = query_db(query, params)
    results = []

    for p in providers:
        p_dict = dict(p)
        # Calculate Haversine distance
        dist = haversine_distance(user_lat, user_lng, p_dict["latitude"], p_dict["longitude"])
        p_dict["distance_km"] = dist

        # Check radius filter
        if dist > radius_km:
            continue

        # Get category details
        cats = query_db(
            """SELECT c.id, c.name, c.slug, c.icon 
               FROM categories c
               JOIN provider_categories pc ON pc.category_id = c.id
               WHERE pc.provider_id = ?""",
            (p_dict["id"],)
        )
        p_dict["categories"] = [dict(c) for c in cats]

        results.append(p_dict)

    # Sorting
    if sort_by == "distance":
        results.sort(key=lambda x: x["distance_km"])
    elif sort_by == "rating":
        results.sort(key=lambda x: x["avg_rating"], reverse=True)
    elif sort_by == "price":
        results.sort(key=lambda x: x["starting_price"])
    else: # Default: 'availability' first, then distance, then rating
        status_rank = {"available": 0, "busy": 1, "offline": 2}
        results.sort(key=lambda x: (status_rank.get(x["availability_status"], 3), x["distance_km"], -x["avg_rating"]))

    return jsonify({
        "count": len(results),
        "user_location": {"lat": user_lat, "lng": user_lng},
        "radius_km": radius_km,
        "providers": results
    }), 200

@provider_bp.route("/<int:provider_id>", methods=["GET"])
def get_provider_profile(provider_id):
    provider = query_db(
        """SELECT p.*, u.name as provider_user_name, u.phone as provider_phone, u.email as provider_email
           FROM providers p
           JOIN users u ON u.id = p.user_id
           WHERE p.id = ?""",
        (provider_id,),
        one=True
    )
    if not provider:
        return jsonify({"error": "Provider not found."}), 404

    p_dict = dict(provider)

    # Categories
    cats = query_db(
        """SELECT c.id, c.name, c.slug, c.icon 
           FROM categories c
           JOIN provider_categories pc ON pc.category_id = c.id
           WHERE pc.provider_id = ?""",
        (provider_id,)
    )
    p_dict["categories"] = [dict(c) for c in cats]

    # Hours
    hours = query_db("SELECT * FROM provider_hours WHERE provider_id = ? ORDER BY day_of_week ASC;", (provider_id,))
    p_dict["hours"] = [dict(h) for h in hours]

    # Rating distribution breakdown (5 stars to 1 star)
    rating_counts = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    reviews_raw = query_db(
        """SELECT r.*, u.name as customer_name 
           FROM reviews r
           JOIN users u ON u.id = r.customer_id
           WHERE r.provider_id = ?
           ORDER BY r.created_at DESC""",
        (provider_id,)
    )
    reviews_list = []
    for r in reviews_raw:
        r_dict = dict(r)
        rating_counts[r_dict["rating"]] = rating_counts.get(r_dict["rating"], 0) + 1
        reviews_list.append(r_dict)

    p_dict["rating_breakdown"] = rating_counts
    p_dict["reviews"] = reviews_list

    # Total completed jobs
    jobs = query_db("SELECT COUNT(*) as cnt FROM bookings WHERE provider_id = ? AND status = 'completed';", (provider_id,), one=True)
    p_dict["completed_jobs_count"] = jobs["cnt"] if jobs else 0

    return jsonify({"provider": p_dict}), 200

@provider_bp.route("/availability", methods=["PUT"])
@require_role("provider")
def update_availability():
    user_id = request.current_user["sub"]
    data = request.get_json() or {}
    status = data.get("availability_status", "").lower()

    if status not in ("available", "busy", "offline"):
        return jsonify({"error": "Invalid status. Allowed values: available, busy, offline."}), 400

    provider = query_db("SELECT id FROM providers WHERE user_id = ?", (user_id,), one=True)
    if not provider:
        return jsonify({"error": "Provider profile not found."}), 404

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    execute_db(
        "UPDATE providers SET availability_status = ?, last_status_change_at = ?, updated_at = ? WHERE id = ?",
        (status, now, now, provider["id"])
    )

    return jsonify({
        "message": f"Availability status updated to '{status}'.",
        "availability_status": status,
        "last_status_change_at": now
    }), 200

@provider_bp.route("/profile", methods=["PUT"])
@require_role("provider")
def update_profile():
    user_id = request.current_user["sub"]
    data = request.get_json() or {}

    provider = query_db("SELECT id, user_id FROM providers WHERE user_id = ?", (user_id,), one=True)
    if not provider:
        return jsonify({"error": "Provider profile not found."}), 404

    provider_id = provider["id"]

    business_name = data.get("business_name")
    description = data.get("description")
    experience_years = data.get("experience_years")
    pricing_note = data.get("pricing_note")
    starting_price = data.get("starting_price")
    service_radius_km = data.get("service_radius_km")
    address_text = data.get("address_text")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    fields = []
    params = []

    if business_name is not None:
        fields.append("business_name = ?")
        params.append(business_name)
    if description is not None:
        fields.append("description = ?")
        params.append(description)
    if experience_years is not None:
        fields.append("experience_years = ?")
        params.append(int(experience_years))
    if pricing_note is not None:
        fields.append("pricing_note = ?")
        params.append(pricing_note)
    if starting_price is not None:
        fields.append("starting_price = ?")
        params.append(float(starting_price))
    if service_radius_km is not None:
        fields.append("service_radius_km = ?")
        params.append(float(service_radius_km))
    if address_text is not None:
        fields.append("address_text = ?")
        params.append(address_text)
    if latitude is not None:
        fields.append("latitude = ?")
        params.append(float(latitude))
    if longitude is not None:
        fields.append("longitude = ?")
        params.append(float(longitude))

    if fields:
        fields.append("updated_at = CURRENT_TIMESTAMP")
        query = f"UPDATE providers SET {', '.join(fields)} WHERE id = ?"
        params.append(provider_id)
        execute_db(query, params)

    # Categories update if provided
    category_ids = data.get("category_ids")
    if category_ids is not None:
        execute_db("DELETE FROM provider_categories WHERE provider_id = ?", (provider_id,))
        for cid in category_ids:
            execute_db("INSERT INTO provider_categories (provider_id, category_id) VALUES (?, ?)", (provider_id, int(cid)))

    return jsonify({"message": "Provider profile updated successfully."}), 200
