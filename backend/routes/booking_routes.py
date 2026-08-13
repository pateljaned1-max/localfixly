from flask import Blueprint, request, jsonify
from database import query_db, execute_db
from auth import require_auth, require_role
import datetime

booking_bp = Blueprint("bookings", __name__)

VALID_TRANSITIONS = {
    "pending": ["accepted", "rejected", "cancelled"],
    "accepted": ["in_progress", "cancelled"],
    "in_progress": ["completed", "cancelled"],
    "completed": [],
    "rejected": [],
    "cancelled": []
}

@booking_bp.route("", methods=["POST"])
@require_role("customer")
def create_booking():
    customer_id = request.current_user["sub"]
    data = request.get_json() or {}

    provider_id = data.get("provider_id")
    category_id = data.get("category_id")
    description = data.get("description", "").strip()
    address_text = data.get("address_text", "").strip()
    preferred_date = data.get("preferred_date", "").strip()
    preferred_time = data.get("preferred_time", "").strip()
    location_lat = data.get("location_lat", 28.6139)
    location_lng = data.get("location_lng", 77.2090)
    photo_url = data.get("photo_url", "")

    if not provider_id or not category_id or not description or not address_text or not preferred_date or not preferred_time:
        return jsonify({"error": "Missing required fields for booking request."}), 400

    provider = query_db("SELECT id FROM providers WHERE id = ?", (provider_id,), one=True)
    if not provider:
        return jsonify({"error": "Selected provider not found."}), 404

    booking_id = execute_db(
        """INSERT INTO bookings 
           (customer_id, provider_id, category_id, description, location_lat, location_lng, address_text, 
            preferred_date, preferred_time, photo_url, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')""",
        (customer_id, provider_id, category_id, description, location_lat, location_lng, address_text, preferred_date, preferred_time, photo_url)
    )

    return jsonify({
        "message": "Service request submitted successfully.",
        "booking_id": booking_id,
        "status": "pending"
    }), 201

@booking_bp.route("", methods=["GET"])
@require_auth
def list_bookings():
    user = request.current_user
    user_id = user["sub"]
    role = user["role"]
    status = request.args.get("status")

    if role == "customer":
        sql = """
            SELECT b.*, p.business_name, p.availability_status, u.name as provider_name, u.phone as provider_phone, u.email as provider_email, c.name as category_name, c.icon as category_icon, r.id as review_id, r.rating as review_rating
            FROM bookings b
            JOIN providers p ON p.id = b.provider_id
            JOIN users u ON u.id = p.user_id
            JOIN categories c ON c.id = b.category_id
            LEFT JOIN reviews r ON r.booking_id = b.id
            WHERE b.customer_id = ?
        """
        params = [user_id]
    elif role == "provider":
        p = query_db("SELECT id FROM providers WHERE user_id = ?", (user_id,), one=True)
        if not p:
            return jsonify({"bookings": []}), 200
        sql = """
            SELECT b.*, u.name as customer_name, u.phone as customer_phone, u.email as customer_email, c.name as category_name, c.icon as category_icon, r.id as review_id, r.rating as review_rating
            FROM bookings b
            JOIN users u ON u.id = b.customer_id
            JOIN categories c ON c.id = b.category_id
            LEFT JOIN reviews r ON r.booking_id = b.id
            WHERE b.provider_id = ?
        """
        params = [p["id"]]
    else: # admin
        sql = """
            SELECT b.*, cust.name as customer_name, prov_u.name as provider_name, p.business_name, c.name as category_name, c.icon as category_icon, r.id as review_id
            FROM bookings b
            JOIN users cust ON cust.id = b.customer_id
            JOIN providers p ON p.id = b.provider_id
            JOIN users prov_u ON prov_u.id = p.user_id
            JOIN categories c ON c.id = b.category_id
            LEFT JOIN reviews r ON r.booking_id = b.id
        """
        params = []

    if status:
        sql += " AND b.status = ?" if "WHERE" in sql else " WHERE b.status = ?"
        params.append(status)

    sql += " ORDER BY b.created_at DESC;"

    rows = query_db(sql, params)
    return jsonify({"bookings": [dict(r) for r in rows]}), 200

@booking_bp.route("/<int:booking_id>", methods=["GET"])
@require_auth
def get_booking(booking_id):
    user = request.current_user
    user_id = user["sub"]

    b = query_db("SELECT * FROM bookings WHERE id = ?", (booking_id,), one=True)
    if not b:
        return jsonify({"error": "Booking not found."}), 404

    b_dict = dict(b)
    # Check authorization
    p = query_db("SELECT user_id FROM providers WHERE id = ?", (b["provider_id"],), one=True)
    provider_user_id = p["user_id"] if p else None

    if user["role"] not in ("admin",) and user_id not in (b["customer_id"], provider_user_id):
        return jsonify({"error": "Forbidden. You are not authorized to view this booking."}), 403

    return jsonify({"booking": b_dict}), 200

@booking_bp.route("/<int:booking_id>/status", methods=["PATCH"])
@require_auth
def update_booking_status(booking_id):
    user = request.current_user
    user_id = user["sub"]
    data = request.get_json() or {}
    new_status = data.get("status", "").lower()
    reason = data.get("reason", "").strip()

    b = query_db("SELECT * FROM bookings WHERE id = ?", (booking_id,), one=True)
    if not b:
        return jsonify({"error": "Booking not found."}), 404

    current_status = b["status"]
    if new_status not in VALID_TRANSITIONS.get(current_status, []):
        return jsonify({"error": f"Invalid state transition from '{current_status}' to '{new_status}'."}), 400

    # Role checks
    p = query_db("SELECT user_id FROM providers WHERE id = ?", (b["provider_id"],), one=True)
    provider_user_id = p["user_id"] if p else None

    if new_status in ("accepted", "rejected", "in_progress", "completed"):
        if user["role"] != "admin" and user_id != provider_user_id:
            return jsonify({"error": "Only the assigned provider or admin can perform this state update."}), 403

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if new_status == "rejected":
        execute_db(
            "UPDATE bookings SET status = 'rejected', cancel_reason = ?, updated_at = ? WHERE id = ?",
            (reason or "Provider unavailable at requested time", now, booking_id)
        )
    else:
        execute_db(
            "UPDATE bookings SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, now, booking_id)
        )

    return jsonify({
        "message": f"Booking status updated from '{current_status}' to '{new_status}'.",
        "booking_id": booking_id,
        "previous_status": current_status,
        "new_status": new_status,
        "updated_at": now
    }), 200

@booking_bp.route("/<int:booking_id>/cancel", methods=["POST"])
@require_auth
def cancel_booking(booking_id):
    user = request.current_user
    user_id = user["sub"]
    data = request.get_json() or {}
    reason = data.get("reason", "").strip()

    if not reason:
        return jsonify({"error": "A cancellation reason is required."}), 400

    b = query_db("SELECT * FROM bookings WHERE id = ?", (booking_id,), one=True)
    if not b:
        return jsonify({"error": "Booking not found."}), 404

    if b["status"] in ("completed", "cancelled", "rejected"):
        return jsonify({"error": f"Cannot cancel a booking in '{b['status']}' state."}), 400

    p = query_db("SELECT user_id FROM providers WHERE id = ?", (b["provider_id"],), one=True)
    provider_user_id = p["user_id"] if p else None

    cancelled_by = None
    if user_id == b["customer_id"]:
        cancelled_by = "customer"
    elif user_id == provider_user_id:
        cancelled_by = "provider"
    elif user["role"] == "admin":
        cancelled_by = "customer"
    else:
        return jsonify({"error": "Forbidden. You are not associated with this booking."}), 403

    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    execute_db(
        "UPDATE bookings SET status = 'cancelled', cancelled_by = ?, cancel_reason = ?, updated_at = ? WHERE id = ?",
        (cancelled_by, reason, now, booking_id)
    )

    return jsonify({
        "message": "Booking cancelled successfully.",
        "booking_id": booking_id,
        "status": "cancelled",
        "cancelled_by": cancelled_by,
        "cancel_reason": reason
    }), 200
