from flask import Blueprint, jsonify
from database import query_db

category_bp = Blueprint("categories", __name__)

@category_bp.route("", methods=["GET"])
def get_categories():
    categories = query_db("SELECT * FROM categories WHERE active = 1 ORDER BY sort_order ASC, name ASC;")
    result = []
    for c in categories:
        cat_dict = dict(c)
        # Count available providers for this category
        cnt = query_db(
            """SELECT COUNT(DISTINCT p.id) as count 
               FROM providers p
               JOIN provider_categories pc ON pc.provider_id = p.id
               WHERE pc.category_id = ? AND p.availability_status = 'available';""",
            (c["id"],),
            one=True
        )
        cat_dict["available_provider_count"] = cnt["count"] if cnt else 0
        result.append(cat_dict)
    
    return jsonify({"categories": result}), 200

@category_bp.route("/<int:cat_id>", methods=["GET"])
def get_category(cat_id):
    cat = query_db("SELECT * FROM categories WHERE id = ? AND active = 1;", (cat_id,), one=True)
    if not cat:
        return jsonify({"error": "Category not found."}), 404
    return jsonify({"category": dict(cat)}), 200
