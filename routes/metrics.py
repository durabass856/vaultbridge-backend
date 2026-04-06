from flask import Blueprint, request
from models.db import query, success, error

metrics_bp = Blueprint("metrics", __name__)

@metrics_bp.route("/", methods=["GET"])
def get_metrics():
    sql = """
        SELECT m.*, s.startup_name 
        FROM startup_operational_metrics m
        JOIN startup s ON m.startup_id = s.startup_id
        ORDER BY m.snapshot_date DESC
    """
    data, err = query(sql)
    return success(data) if not err else error(err)

@metrics_bp.route("/", methods=["POST"])
def create_metric():
    b = request.get_json()

    if not b.get("startup_id"):
        return error("startup_id required")

    sql = """
        INSERT INTO startup_operational_metrics
        (startup_id, snapshot_date, monthly_revenue_usd, monthly_burn_usd, runway_months,
         gross_margin_pct, customer_count, mrr_usd, churn_rate_pct, nps_score, source)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    data, err = query(sql, (
        b["startup_id"],
        b.get("snapshot_date"),
        b.get("monthly_revenue_usd"),
        b.get("monthly_burn_usd"),
        b.get("runway_months"),
        b.get("gross_margin_pct"),
        b.get("customer_count"),
        b.get("mrr_usd"),
        b.get("churn_rate_pct"),
        b.get("nps_score"),
        b.get("source", "Self-reported")
    ), fetch="none")

    return success({"metric_id": data["lastrowid"]}, "Metrics logged", 201) if not err else error(err)

@metrics_bp.route("/<int:mid>", methods=["DELETE"])
def delete_metric(mid):
    data, err = query("DELETE FROM startup_operational_metrics WHERE metric_id=%s", (mid,), fetch="none")
    return success(message="Metric deleted") if not err else error(err)
