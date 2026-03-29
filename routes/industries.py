from flask import Blueprint, request
from models.db import query, success, error

industries_bp = Blueprint("industries", __name__)

@industries_bp.route("/", methods=["GET"])
def get_industries():
    data, err = query("SELECT * FROM industry ORDER BY industry_name")
    return success(data) if not err else error(err)

@industries_bp.route("/", methods=["POST"])
def create_industry():
    b = request.get_json()
    sql = "INSERT INTO industry (industry_name,parent_industry_id,description) VALUES (%s,%s,%s)"
    data, err = query(sql,(b.get("industry_name"),b.get("parent_industry_id"),
                           b.get("description")),fetch="none")
    return (success({"industry_id":data["lastrowid"]},"Industry created",201) if not err else error(err))
