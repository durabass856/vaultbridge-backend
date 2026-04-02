from flask import Blueprint, request
from models.db import query, success, error

startups_bp = Blueprint("startups", __name__)


# GET /api/startups
@startups_bp.route("/", methods=["GET"])
def get_all():
    sql = """
        SELECT s.*,
               i.industry_name,
               CONCAT(l.city, ', ', l.country) AS location_display
        FROM startup s
        LEFT JOIN industry i ON s.industry_id = i.industry_id
        LEFT JOIN location l ON s.location_id = l.location_id
        ORDER BY s.created_at DESC
    """
    data, err = query(sql)
    if err: return error(err)
    return success(data)


# GET /api/startups/<id>
@startups_bp.route("/<int:sid>", methods=["GET"])
def get_one(sid):
    sql = """
        SELECT s.*,
               i.industry_name,
               CONCAT(l.city, ', ', l.country) AS location_display
        FROM startup s
        LEFT JOIN industry i ON s.industry_id = i.industry_id
        LEFT JOIN location l ON s.location_id = l.location_id
        WHERE s.startup_id = %s
    """
    data, err = query(sql, (sid,), fetch="one")
    if err: return error(err)
    if not data: return error("Startup not found", 404)
    return success(data)


# POST /api/startups
@startups_bp.route("/", methods=["POST"])
def create():
    b = request.get_json()

    if not b or not b.get("startup_name"):
        return error("startup_name is required")

    # 1️⃣ Insert startup
    sql = """
        INSERT INTO startup
          (startup_name, tagline, industry_id, location_id, website,
           founded_year, registration_number, annual_revenue_usd,
           profit_loss_usd, num_employees, total_funding_usd, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    args = (
        b.get("startup_name"), b.get("tagline"),
        b.get("industry_id"), b.get("location_id"),
        b.get("website"), b.get("founded_year"),
        b.get("registration_number"), b.get("annual_revenue_usd"),
        b.get("profit_loss_usd"), b.get("num_employees"),
        b.get("total_funding_usd", 0), b.get("status", "Active"),
    )

    data, err = query(sql, args, fetch="none")
    if err:
        return error(err)

    startup_id = data["lastrowid"]

    awards = b.get("awards")  # expect list of objects

    if awards:
        award_sql = """
            INSERT INTO startup_award
            (startup_id, award_name, awarding_body, award_date, award_category)
            VALUES (%s,%s,%s,%s,%s)
        """

        for award in awards:
            query(award_sql, (
                startup_id,
                award.get("award_name"),
                award.get("awarding_body"),
                award.get("award_date"),
                award.get("award_category")
            ), fetch="none")

    return success({"startup_id": startup_id}, "Startup created", 201)


# PUT /api/startups/<id>
@startups_bp.route("/<int:sid>", methods=["PUT"])
def update(sid):
    b = request.get_json()
    sql = """
        UPDATE startup SET
          startup_name=%s, tagline=%s, industry_id=%s, location_id=%s,
          website=%s, founded_year=%s, registration_number=%s,
          annual_revenue_usd=%s, profit_loss_usd=%s, num_employees=%s,
          total_funding_usd=%s, status=%s
        WHERE startup_id=%s
    """
    args = (
        b.get("startup_name"), b.get("tagline"),
        b.get("industry_id"), b.get("location_id"),
        b.get("website"), b.get("founded_year"),
        b.get("registration_number"), b.get("annual_revenue_usd"),
        b.get("profit_loss_usd"), b.get("num_employees"),
        b.get("total_funding_usd"), b.get("status"), sid,
    )
    data, err = query(sql, args, fetch="none")
    if err: return error(err)
    return success(message="Startup updated")


# DELETE /api/startups/<id>
@startups_bp.route("/<int:sid>", methods=["DELETE"])
def delete(sid):
    data, err = query("DELETE FROM startup WHERE startup_id=%s", (sid,), fetch="none")
    if err: return error(err)
    return success(message="Startup deleted")
