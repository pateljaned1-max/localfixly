from flask import Blueprint, request, jsonify
from database import query_db, execute_db
from auth import require_role

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/stats", methods=["GET"])
@require_role("admin")
def get_stats():
    total_users = query_db("SELECT COUNT(*) as cnt FROM users;", one=True)["cnt"]
    total_customers = query_db("SELECT COUNT(*) as cnt FROM users WHERE role = 'customer';", one=True)["cnt"]
    total_providers = query_db("SELECT COUNT(*) as cnt FROM providers;", one=True)["cnt"]
    active_providers = query_db("SELECT COUNT(*) as cnt FROM providers WHERE availability_status = 'available';", one=True)["cnt"]
    pending_verifications = query_db("SELECT COUNT(*) as cnt FROM providers WHERE verification_status = 'pending';", one=True)["cnt"]
    
    total_bookings = query_db("SELECT COUNT(*) as cnt FROM bookings;", one=True)["cnt"]
    bookings_completed = query_db("SELECT COUNT(*) as cnt FROM bookings WHERE status = 'completed';", one=True)["cnt"]
    
    # Bookings this week (last 7 days)
    bookings_this_week = query_db(
        "SELECT COUNT(*) as cnt FROM bookings WHERE created_at >= datetime('now', '-7 days');",
        one=True
    )["cnt"]
    
    avg_rating_res = query_db("SELECT AVG(rating) as avg_r FROM reviews;", one=True)
    avg_rating = round(avg_rating_res["avg_r"], 2) if avg_rating_res and avg_rating_res["avg_r"] else 0.0

    pending_reports = query_db("SELECT COUNT(*) as cnt FROM reports WHERE status = 'pending';", one=True)["cnt"]

    return jsonify({
        "stats": {
            "total_users": total_users,
            "total_customers": total_customers,
            "total_providers": total_providers,
            "active_available_providers": active_providers,
            "pending_verifications": pending_verifications,
            "total_bookings": total_bookings,
            "bookings_completed": bookings_completed,
            "bookings_this_week": bookings_this_week,
            "platform_avg_rating": avg_rating,
            "pending_reports": pending_reports
        }
    }), 200

@admin_bp.route("/providers", methods=["GET"])
@require_role("admin")
def list_providers():
    status = request.args.get("status")
    sql = """
        SELECT p.*, u.name as provider_user_name, u.email, u.phone
        FROM providers p
        JOIN users u ON u.id = p.user_id
    """
    params = []
    if status:
        sql += " WHERE p.verification_status = ?"
        params.append(status)
    sql += " ORDER BY p.created_at DESC;"

    providers = query_db(sql, params)
    return jsonify({"providers": [dict(p) for p in providers]}), 200

@admin_bp.route("/providers/<int:provider_id>/verify", methods=["PATCH"])
@require_role("admin")
def verify_provider(provider_id):
    data = request.get_json() or {}
    status = data.get("status", "").lower() # 'approved' or 'rejected'

    if status not in ("approved", "rejected", "pending"):
        return jsonify({"error": "Invalid verification status. Must be 'approved', 'rejected', or 'pending'."}), 400

    provider = query_db("SELECT id FROM providers WHERE id = ?", (provider_id,), one=True)
    if not provider:
        return jsonify({"error": "Provider not found."}), 404

    is_verified = 1 if status == "approved" else 0
    execute_db(
        "UPDATE providers SET verified = ?, verification_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (is_verified, status, provider_id)
    )

    return jsonify({
        "message": f"Provider verification status updated to '{status}'.",
        "provider_id": provider_id,
        "verified": bool(is_verified),
        "verification_status": status
    }), 200

@admin_bp.route("/users", methods=["GET"])
@require_role("admin")
def list_users():
    role = request.args.get("role")
    sql = "SELECT id, name, email, phone, role, created_at FROM users"
    params = []
    if role:
        sql += " WHERE role = ?"
        params.append(role)
    sql += " ORDER BY created_at DESC;"

    users = query_db(sql, params)
    return jsonify({"users": [dict(u) for u in users]}), 200

@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@require_role("admin")
def delete_user(user_id):
    user = query_db("SELECT id, role FROM users WHERE id = ?", (user_id,), one=True)
    if not user:
        return jsonify({"error": "User not found."}), 404

    if user["role"] == "admin":
        return jsonify({"error": "Cannot delete administrator accounts."}), 400

    execute_db("DELETE FROM users WHERE id = ?", (user_id,))
    return jsonify({"message": f"User #{user_id} deleted successfully."}), 200

@admin_bp.route("/categories", methods=["POST"])
@require_role("admin")
def create_category():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    slug = data.get("slug", "").strip().lower()
    icon = data.get("icon", "🔧").strip()
    description = data.get("description", "").strip()

    if not name or not slug:
        return jsonify({"error": "Name and slug are required."}), 400

    cat_id = execute_db(
        "INSERT INTO categories (name, slug, icon, description, active, sort_order) VALUES (?, ?, ?, ?, 1, 99)",
        (name, slug, icon, description)
    )
    return jsonify({"message": "Category created successfully.", "category_id": cat_id}), 201

@admin_bp.route("/categories/<int:cat_id>", methods=["PUT"])
@require_role("admin")
def update_category(cat_id):
    data = request.get_json() or {}
    active = data.get("active")
    name = data.get("name")
    icon = data.get("icon")
    description = data.get("description")

    cat = query_db("SELECT id FROM categories WHERE id = ?", (cat_id,), one=True)
    if not cat:
        return jsonify({"error": "Category not found."}), 404

    fields, params = [], []
    if active is not None:
        fields.append("active = ?")
        params.append(1 if active else 0)
    if name is not None:
        fields.append("name = ?")
        params.append(name)
    if icon is not None:
        fields.append("icon = ?")
        params.append(icon)
    if description is not None:
        fields.append("description = ?")
        params.append(description)

    if fields:
        params.append(cat_id)
        execute_db(f"UPDATE categories SET {', '.join(fields)} WHERE id = ?", params)

    return jsonify({"message": "Category updated successfully."}), 200

@admin_bp.route("/reports", methods=["GET"])
@require_role("admin")
def list_reports():
    reports = query_db(
        """SELECT rep.*, reporter.name as reporter_name, ruser.name as reported_user_name, p.business_name as reported_provider_business
           FROM reports rep
           JOIN users reporter ON reporter.id = rep.reporter_id
           LEFT JOIN users ruser ON ruser.id = rep.reported_user_id
           LEFT JOIN providers p ON p.id = rep.reported_provider_id
           ORDER BY rep.created_at DESC;"""
    )
    return jsonify({"reports": [dict(r) for r in reports]}), 200

@admin_bp.route("/reports/<int:report_id>", methods=["PATCH"])
@require_role("admin")
def update_report(report_id):
    data = request.get_json() or {}
    status = data.get("status", "resolved")

    execute_db("UPDATE reports SET status = ? WHERE id = ?", (status, report_id))
    return jsonify({"message": f"Report status updated to '{status}'."}), 200

@admin_bp.route("/reviews", methods=["GET"])
@require_role("admin")
def list_reviews_moderation():
    reviews = query_db(
        """SELECT r.*, u.name as customer_name, p.business_name
           FROM reviews r
           JOIN users u ON u.id = r.customer_id
           JOIN providers p ON p.id = r.provider_id
           ORDER BY r.created_at DESC;"""
    )
    return jsonify({"reviews": [dict(rev) for rev in reviews]}), 200

@admin_bp.route("/reviews/<int:review_id>", methods=["DELETE"])
@require_role("admin")
def delete_review(review_id):
    rev = query_db("SELECT provider_id FROM reviews WHERE id = ?", (review_id,), one=True)
    if not rev:
        return jsonify({"error": "Review not found."}), 404

    provider_id = rev["provider_id"]
    execute_db("DELETE FROM reviews WHERE id = ?", (review_id,))

    # Recalculate provider avg rating
    stats = query_db("SELECT AVG(rating) as avg_r, COUNT(*) as cnt FROM reviews WHERE provider_id = ?", (provider_id,), one=True)
    new_avg = round(stats["avg_r"], 1) if stats and stats["avg_r"] else 0.0
    new_cnt = stats["cnt"] if stats else 0

    execute_db("UPDATE providers SET avg_rating = ?, review_count = ? WHERE id = ?", (new_avg, new_cnt, provider_id))

    return jsonify({"message": "Review deleted and provider ratings updated."}), 200
