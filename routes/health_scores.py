from flask import Blueprint, request
from models.db import query, success, error

health_bp = Blueprint("health_scores", __name__)

@health_bp.route("/", methods=["GET"])
def get_health():
    sql = """
        SELECT h.*, s.startup_name 
        FROM startup_health_score h
        JOIN startup s ON h.startup_id = s.startup_id
        ORDER BY h.score_date DESC
    """
    data, err = query(sql)
    return success(data) if not err else error(err)

@health_bp.route("/", methods=["POST"])
def create_health():
    b = request.get_json()

    sql = """
        INSERT INTO startup_health_score
        (startup_id, score_date, financial_score, team_score, product_score,
         market_score, overall_score, risk_flag, scored_by, notes)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    data, err = query(sql, (
        b.get("startup_id"),
        b.get("score_date"),
        b.get("financial_score"),
        b.get("team_score"),
        b.get("product_score"),
        b.get("market_score"),
        b.get("overall_score"),
        b.get("risk_flag", "Green"),
        b.get("scored_by"),
        b.get("notes")
    ), fetch="none")

    return success({"score_id": data["lastrowid"]}, "Health score added", 201) if not err else error(err)

@health_bp.route("/<int:hid>", methods=["DELETE"])
def delete_health(hid):
    data, err = query("DELETE FROM startup_health_score WHERE score_id=%s", (hid,), fetch="none")
    return success(message="Health score deleted") if not err else error(err)
