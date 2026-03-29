from flask import Blueprint, request
from models.db import query, success, error

product_categories_bp = Blueprint("product_categories", __name__)

@product_categories_bp.route("/", methods=["GET"])
def get_product_categories():
    data, err = query("SELECT * FROM product_category ORDER BY category_name")
    return success(data) if not err else error(err)

@product_categories_bp.route("/", methods=["POST"])
def create_product_category():
    b = request.get_json()
    sql = "INSERT INTO product_category (category_name, parent_category_id) VALUES (%s, %s)"
    data, err = query(sql, (b.get("category_name"), b.get("parent_category_id")), fetch="none")
    return (success({"category_id": data["lastrowid"]}, "Product category created", 201) if not err else error(err))
