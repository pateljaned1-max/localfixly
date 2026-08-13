from flask import Blueprint, request, jsonify
from database import query_db, execute_db
from auth import require_auth, require_role

report_bp = Blueprint("reports", __name__)

@report_bp.route("", methods=["POST"])
@require_auth
def submit_report():
    reporter_id = request.current_user["sub"]
    data = request.get_json() or {}

    reported_user_id = data.get("reported_user_id")
    reported_provider_id = data.get("reported_provider_id")
    reason = data.get("reason", "").strip()

    if not reason:
        return jsonify({"error": "A detailed reason for the report is required."}), 400

    if not reported_user_id and not reported_provider_id:
        return jsonify({"error": "Must specify either reported_user_id or reported_provider_id."}), 400

    report_id = execute_db(
        "INSERT INTO reports (reporter_id, reported_user_id, reported_provider_id, reason, status) VALUES (?, ?, ?, ?, 'pending')",
        (reporter_id, reported_user_id, reported_provider_id, reason)
    )

    return jsonify({
        "message": "Report submitted. Our moderation team will investigate.",
        "report_id": report_id
    }), 201
