from flask import Blueprint, request
from models.db import query, success, error

locations_bp = Blueprint("locations", __name__)

@locations_bp.route("/", methods=["GET"])
def get_locations():
    data, err = query("SELECT * FROM location ORDER BY country, city")
    return success(data) if not err else error(err)

@locations_bp.route("/", methods=["POST"])
def create_location():
    b = request.get_json()
    sql = "INSERT INTO location (city,state,country,zip_code,region) VALUES (%s,%s,%s,%s,%s)"
    data, err = query(sql,(b.get("city"),b.get("state"),b.get("country"),
                           b.get("zip_code"),b.get("region")),fetch="none")
    return (success({"location_id":data["lastrowid"]},"Location created",201) if not err else error(err))
