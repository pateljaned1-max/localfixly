import os
import sys

# Ensure backend root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from database import init_db, query_db
from utils.seed import seed_database
from routes.auth_routes import auth_bp
from routes.category_routes import category_bp
from routes.provider_routes import provider_bp
from routes.booking_routes import booking_bp
from routes.review_routes import review_bp
from routes.report_routes import report_bp
from routes.admin_routes import admin_bp

from config import CORS_ORIGINS, SEED_DEMO_DATA

PROJECT_ROOT = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path=None)
CORS(app, resources={r"/api/*": {"origins": CORS_ORIGINS}})

# Register blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(category_bp, url_prefix="/api/categories")
app.register_blueprint(provider_bp, url_prefix="/api/providers")
app.register_blueprint(booking_bp, url_prefix="/api/bookings")
app.register_blueprint(review_bp, url_prefix="/api/reviews")
app.register_blueprint(report_bp, url_prefix="/api/reports")
app.register_blueprint(admin_bp, url_prefix="/api/admin")

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "app": "LocalFix API", "version": "1.0.0"}), 200

@app.route("/favicon.ico")
def favicon():
    return "", 204

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    return jsonify({
        "error": e.name,
        "message": e.description
    }), e.code

@app.errorhandler(Exception)
def handle_global_exception(e):
    if isinstance(e, HTTPException):
        return handle_http_exception(e)
    app.logger.error(f"Unhandled Exception: {str(e)}", exc_info=True)
    return jsonify({
        "error": "Internal Server Error",
        "message": str(e)
    }), 500

# Serve static frontend files
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path.startswith("api/") or path == "api":
        return jsonify({"error": "API endpoint not found."}), 404
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")

def bootstrap():
    init_db()
    # Check if database has categories/users, if not seed it conditionally based on config
    res = query_db("SELECT COUNT(*) as cnt FROM categories;", one=True)
    if (not res or res["cnt"] == 0) and SEED_DEMO_DATA:
        print("Empty database detected. Automatic initial seed executing...")
        seed_database()

bootstrap()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting LocalFix Server on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
