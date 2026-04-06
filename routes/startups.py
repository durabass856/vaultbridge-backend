from flask import Blueprint, request
from models.db import get_connection, query, success, error

startups_bp = Blueprint("startups", __name__)

# ─────────────────────────────────────────────
#  GET ALL STARTUPS (UPGRADED)
# ─────────────────────────────────────────────
@startups_bp.route("/", methods=["GET"])
def get_all():
    sql = """
        SELECT 
            s.*,
            i.industry_name,
            CONCAT(l.city, ', ', l.country) AS location_display,

            -- 🔥 NEW (IMPORTANT)
            fn_latest_valuation(s.startup_id) AS latest_valuation_usd,
            fn_startup_health_risk(s.startup_id) AS health_risk,
            fn_deal_count_for_startup(s.startup_id) AS closed_deals

        FROM startup s
        LEFT JOIN industry i ON s.industry_id = i.industry_id
        LEFT JOIN location l ON s.location_id = l.location_id
        ORDER BY s.created_at DESC
    """
    data, err = query(sql)
    if err: return error(err)
    return success(data)


# ─────────────────────────────────────────────
#  GET ONE STARTUP (UPGRADED)
# ─────────────────────────────────────────────
@startups_bp.route("/<int:sid>", methods=["GET"])
def get_one(sid):
    sql = """
        SELECT 
            s.*,
            i.industry_name,
            CONCAT(l.city, ', ', l.country) AS location_display,

            fn_latest_valuation(s.startup_id) AS latest_valuation_usd,
            fn_startup_health_risk(s.startup_id) AS health_risk,
            fn_deal_count_for_startup(s.startup_id) AS closed_deals

        FROM startup s
        LEFT JOIN industry i ON s.industry_id = i.industry_id
        LEFT JOIN location l ON s.location_id = l.location_id
        WHERE s.startup_id = %s
    """
    data, err = query(sql, (sid,), fetch="one")
    if err: return error(err)
    if not data: return error("Startup not found", 404)
    return success(data)


# ─────────────────────────────────────────────
#  FULL REPORT (BEST ENDPOINT)
# ─────────────────────────────────────────────
@startups_bp.route("/<int:sid>/full-report", methods=["GET"])
def get_full_report(sid):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("CALL sp_startup_full_report(%s)", (sid,))

        startup_info = cur.fetchone()

        cur.nextset()
        deals = cur.fetchall()

        cur.nextset()
        founders = cur.fetchall()

        cur.nextset()
        metrics = cur.fetchall()

        cur.nextset()
        health_scores = cur.fetchall()

        while cur.nextset():
            pass

        cur.close()
        conn.close()

        return success({
            "startup_info": startup_info,
            "deals": deals or [],
            "founders": founders or [],
            "metrics": metrics or [],
            "health_scores": health_scores or [],
        })

    except Exception as exc:
        return error(str(exc), 500)


# ─────────────────────────────────────────────
#  STATUS HISTORY
# ─────────────────────────────────────────────
@startups_bp.route("/<int:sid>/status-history", methods=["GET"])
def get_status_history(sid):
    sql = """
        SELECT * FROM startup_status_history
        WHERE startup_id = %s
        ORDER BY changed_date DESC
    """
    data, err = query(sql, (sid,))
    if err: return error(err)
    return success(data)


# ─────────────────────────────────────────────
#  CURSOR SUMMARY
# ─────────────────────────────────────────────
@startups_bp.route("/<int:sid>/cursor-summary", methods=["GET"])
def get_cursor_summary(sid):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("CALL sp_cursor_startup_metric_summary(%s)", (sid,))
        data = cur.fetchone()

        while cur.nextset():
            pass

        cur.close()
        conn.close()

        return success(data or {})

    except Exception as exc:
        return error(str(exc), 500)


# ─────────────────────────────────────────────
#  CREATE STARTUP
# ─────────────────────────────────────────────
@startups_bp.route("/", methods=["POST"])
def create():
    b = request.get_json()
    required = ["startup_name", "founded_year"]

    for f in required:
        if not b.get(f):
            return error(f"{f} is required")

    sql = """
        INSERT INTO startup
          (startup_name, tagline, industry_id, location_id, website,
           founded_year, registration_number, annual_revenue_usd,
           profit_loss_usd, num_employees, total_funding_usd, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    args = (
        b.get("startup_name"),
        b.get("tagline"),
        b.get("industry_id"),
        b.get("location_id"),
        b.get("website"),
        b.get("founded_year"),
        b.get("registration_number"),
        b.get("annual_revenue_usd"),
        b.get("profit_loss_usd"),
        b.get("num_employees"),
        b.get("total_funding_usd", 0),
        b.get("status", "Active"),
    )

    data, err = query(sql, args, fetch="none")
    if err: return error(err)

    return success({"startup_id": data["lastrowid"]}, "Startup created", 201)


# ─────────────────────────────────────────────
#  UPDATE STARTUP
# ─────────────────────────────────────────────
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
        b.get("startup_name"),
        b.get("tagline"),
        b.get("industry_id"),
        b.get("location_id"),
        b.get("website"),
        b.get("founded_year"),
        b.get("registration_number"),
        b.get("annual_revenue_usd"),
        b.get("profit_loss_usd"),
        b.get("num_employees"),
        b.get("total_funding_usd"),
        b.get("status"),
        sid,
    )

    data, err = query(sql, args, fetch="none")
    if err: return error(err)

    return success(message="Startup updated")


# ─────────────────────────────────────────────
#  DELETE STARTUP
# ─────────────────────────────────────────────
@startups_bp.route("/<int:sid>", methods=["DELETE"])
def delete(sid):
    data, err = query("DELETE FROM startup WHERE startup_id=%s", (sid,), fetch="none")
    if err: return error(err)
    return success(message="Startup deleted")
