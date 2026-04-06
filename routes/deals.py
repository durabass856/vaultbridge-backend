from flask import Blueprint, request
from models.db import query, success, error

deals_bp = Blueprint("deals", __name__)

@deals_bp.route("/", methods=["GET"])
def get_all():
    sql = """
        SELECT d.*, s.startup_name,
               GROUP_CONCAT(CONCAT(sh.first_name,' ',sh.last_name) SEPARATOR ', ') AS sharks
        FROM deal d
        LEFT JOIN startup s ON d.startup_id = s.startup_id
        LEFT JOIN deal_shark ds ON d.deal_id = ds.deal_id
        LEFT JOIN shark sh ON ds.shark_id = sh.shark_id
        GROUP BY d.deal_id
        ORDER BY d.created_at DESC
    """
    data, err = query(sql)
    return success(data) if not err else error(err)

@deals_bp.route("/<int:did>", methods=["GET"])
def get_one(did):
    deal, err = query("""
        SELECT d.*, s.startup_name FROM deal d
        LEFT JOIN startup s ON d.startup_id = s.startup_id
        WHERE d.deal_id=%s""", (did,), fetch="one")

    if err: return error(err)
    if not deal: return error("Deal not found", 404)

    sharks, _ = query("""
        SELECT ds.*, sh.first_name, sh.last_name
        FROM deal_shark ds JOIN shark sh ON ds.shark_id=sh.shark_id
        WHERE ds.deal_id=%s""", (did,))

    deal["deal_sharks"] = sharks or []
    return success(deal)

@deals_bp.route("/", methods=["POST"])
def create():
    b = request.get_json()

    if not b.get("startup_id"):
        return error("startup_id is required")

    sql = """INSERT INTO deal
             (startup_id,deal_amount_usd,deal_equity_percent,deal_type,
              royalty_per_unit,loan_interest_rate,handshake_date,closed_date,
              deal_status,deal_notes)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    args = (
        b["startup_id"],
        b.get("deal_amount_usd"),
        b.get("deal_equity_percent"),
        b.get("deal_type", "Equity"),
        b.get("royalty_per_unit"),
        b.get("loan_interest_rate"),
        b.get("handshake_date"),
        b.get("closed_date"),
        b.get("deal_status", "Handshake"),
        b.get("deal_notes")
    )

    data, err = query(sql, args, fetch="none")
    if err: return error(err)

    return success({"deal_id": data["lastrowid"]}, "Deal created", 201)
