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
    if err: return error(err)
    return success(data)

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
    if not b.get("startup_id"): return error("startup_id is required")
    sql = """INSERT INTO deal
             (startup_id,deal_amount_usd,deal_equity_percent,deal_type,
              royalty_per_unit,loan_interest_rate,handshake_date,closed_date,
              deal_status,deal_notes)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    args = (b["startup_id"],b.get("deal_amount_usd"),b.get("deal_equity_percent"),
            b.get("deal_type","Equity"),b.get("royalty_per_unit"),
            b.get("loan_interest_rate"),b.get("handshake_date"),b.get("closed_date"),
            b.get("deal_status","Handshake"),b.get("deal_notes"))
    data, err = query(sql, args, fetch="none")
    if err: return error(err)
    did = data["lastrowid"]
    # Link sharks
    for sh in b.get("sharks", []):
        query("""INSERT INTO deal_shark
                 (deal_id,shark_id,shark_contribution_usd,shark_equity_percent,is_lead_investor)
                 VALUES (%s,%s,%s,%s,%s)""",
              (did, sh["shark_id"], sh.get("contribution",0),
               sh.get("equity",0), sh.get("is_lead",0)), fetch="none")
    return success({"deal_id": did}, "Deal created", 201)

@deals_bp.route("/<int:did>", methods=["PUT"])
def update(did):
    b = request.get_json()
    sql = """UPDATE deal SET startup_id=%s,deal_amount_usd=%s,deal_equity_percent=%s,
             deal_type=%s,royalty_per_unit=%s,loan_interest_rate=%s,handshake_date=%s,
             closed_date=%s,deal_status=%s,deal_notes=%s WHERE deal_id=%s"""
    args = (b.get("startup_id"),b.get("deal_amount_usd"),b.get("deal_equity_percent"),
            b.get("deal_type"),b.get("royalty_per_unit"),b.get("loan_interest_rate"),
            b.get("handshake_date"),b.get("closed_date"),b.get("deal_status"),
            b.get("deal_notes"),did)
    data, err = query(sql, args, fetch="none")
    if err: return error(err)
    return success(message="Deal updated")

@deals_bp.route("/<int:did>", methods=["DELETE"])
def delete(did):
    data, err = query("DELETE FROM deal WHERE deal_id=%s", (did,), fetch="none")
    if err: return error(err)
    return success(message="Deal deleted")
