from flask import Blueprint, request
from models.db import query, success, error

valuations_bp = Blueprint("valuations", __name__)

@valuations_bp.route("/", methods=["GET"])
def get_valuations():
    sql = """SELECT v.*, s.startup_name FROM startup_valuation_history v
             JOIN startup s ON v.startup_id=s.startup_id ORDER BY v.valuation_date DESC"""
    data, err = query(sql)
    return success(data) if not err else error(err)

@valuations_bp.route("/", methods=["POST"])
def create_valuation():
    b = request.get_json()
    sql = """INSERT INTO startup_valuation_history
             (startup_id,valuation_date,valuation_usd,valuation_method,source)
             VALUES (%s,%s,%s,%s,%s)"""
    data, err = query(sql,(b.get("startup_id"),b.get("valuation_date"),b.get("valuation_usd"),
                           b.get("valuation_method"),b.get("source")),fetch="none")
    return (success({"valuation_id":data["lastrowid"]},"Valuation added",201) if not err else error(err))

@valuations_bp.route("/<int:vid>", methods=["DELETE"])
def delete_valuation(vid):
    data, err = query("DELETE FROM startup_valuation_history WHERE valuation_id=%s",(vid,),fetch="none")
    return success(message="Valuation deleted") if not err else error(err)
