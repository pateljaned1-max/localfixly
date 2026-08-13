from flask import Blueprint, request, jsonify
from database import query_db, execute_db
from auth import require_role

review_bp = Blueprint("reviews", __name__)

@review_bp.route("", methods=["POST"])
@require_role("customer")
def create_review():
    customer_id = request.current_user["sub"]
    data = request.get_json() or {}

    booking_id = data.get("booking_id")
    rating = data.get("rating")
    review_text = data.get("review", "").strip()

    if not booking_id or not rating or not review_text:
        return jsonify({"error": "Booking ID, rating (1-5), and review text are required."}), 400

    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            raise ValueError()
    except ValueError:
        return jsonify({"error": "Rating must be an integer between 1 and 5."}), 400

    booking = query_db("SELECT * FROM bookings WHERE id = ?", (booking_id,), one=True)
    if not booking:
        return jsonify({"error": "Booking not found."}), 404

    if booking["customer_id"] != customer_id:
        return jsonify({"error": "Forbidden. You can only review your own completed bookings."}), 403

    if booking["status"] != "completed":
        return jsonify({"error": f"Reviews are only permitted for completed bookings. Current status: '{booking['status']}'."}), 400

    existing = query_db("SELECT id FROM reviews WHERE booking_id = ?", (booking_id,), one=True)
    if existing:
        return jsonify({"error": "A review has already been submitted for this booking."}), 409

    provider_id = booking["provider_id"]

    review_id = execute_db(
        "INSERT INTO reviews (booking_id, customer_id, provider_id, rating, review) VALUES (?, ?, ?, ?, ?)",
        (booking_id, customer_id, provider_id, rating, review_text)
    )

    # Recalculate provider avg rating & review count
    stats = query_db(
        "SELECT AVG(rating) as avg_r, COUNT(*) as cnt FROM reviews WHERE provider_id = ?",
        (provider_id,),
        one=True
    )
    new_avg = round(stats["avg_r"], 1) if stats and stats["avg_r"] else 0.0
    new_cnt = stats["cnt"] if stats else 0

    execute_db(
        "UPDATE providers SET avg_rating = ?, review_count = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (new_avg, new_cnt, provider_id)
    )

    return jsonify({
        "message": "Review submitted successfully.",
        "review_id": review_id,
        "provider_avg_rating": new_avg,
        "provider_review_count": new_cnt
    }), 201

@review_bp.route("/provider/<int:provider_id>", methods=["GET"])
def get_provider_reviews(provider_id):
    reviews = query_db(
        """SELECT r.*, u.name as customer_name 
           FROM reviews r
           JOIN users u ON u.id = r.customer_id
           WHERE r.provider_id = ?
           ORDER BY r.created_at DESC""",
        (provider_id,)
    )
    return jsonify({"reviews": [dict(r) for r in reviews]}), 200
