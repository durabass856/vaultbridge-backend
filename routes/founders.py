# ── founders.py ──────────────────────────────────────────────
from flask import Blueprint, request
from models.db import query, success, error

founders_bp = Blueprint("founders", __name__)

@founders_bp.route("/", methods=["GET"])
def get_all():
    sql = """
        SELECT f.*,
               fs.startup_id, s.startup_name, fs.role, fs.equity_percentage
        FROM founder f
        LEFT JOIN founder_startup fs ON f.founder_id = fs.founder_id
        LEFT JOIN startup s ON fs.startup_id = s.startup_id
        ORDER BY f.founder_id DESC
    """
    data, err = query(sql)
    if err: return error(err)
    return success(data)

@founders_bp.route("/<int:fid>", methods=["GET"])
def get_one(fid):
    data, err = query("SELECT * FROM founder WHERE founder_id=%s", (fid,), fetch="one")
    if err: return error(err)
    if not data: return error("Founder not found", 404)
    return success(data)

@founders_bp.route("/", methods=["POST"])
def create():
    b = request.get_json()
    if not b.get("first_name"): return error("first_name is required")
    sql = """INSERT INTO founder
             (first_name,last_name,email,phone,date_of_birth,gender,nationality,linkedin_url,bio)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    args = (b.get("first_name"),b.get("last_name"),b.get("email"),b.get("phone"),
            b.get("date_of_birth"),b.get("gender"),b.get("nationality"),
            b.get("linkedin_url"),b.get("bio"))
    data, err = query(sql, args, fetch="none")
    if err: return error(err)
    fid = data["lastrowid"]
    # Link to startup if provided
    if b.get("startup_id"):
        sql2 = """INSERT INTO founder_startup
                  (founder_id,startup_id,role,equity_percentage,joined_date,is_primary_contact)
                  VALUES (%s,%s,%s,%s,%s,%s)"""
        query(sql2, (fid,b["startup_id"],b.get("role","Founder"),
                     b.get("equity_percentage"),b.get("joined_date"),
                     b.get("is_primary_contact",0)), fetch="none")
    return success({"founder_id": fid}, "Founder created", 201)

@founders_bp.route("/<int:fid>", methods=["PUT"])
def update(fid):
    b = request.get_json()
    sql = """UPDATE founder SET first_name=%s,last_name=%s,email=%s,phone=%s,
             date_of_birth=%s,gender=%s,nationality=%s,linkedin_url=%s,bio=%s
             WHERE founder_id=%s"""
    args = (b.get("first_name"),b.get("last_name"),b.get("email"),b.get("phone"),
            b.get("date_of_birth"),b.get("gender"),b.get("nationality"),
            b.get("linkedin_url"),b.get("bio"),fid)
    data, err = query(sql, args, fetch="none")
    if err: return error(err)
    return success(message="Founder updated")

@founders_bp.route("/<int:fid>", methods=["DELETE"])
def delete(fid):
    data, err = query("DELETE FROM founder WHERE founder_id=%s", (fid,), fetch="none")
    if err: return error(err)
    return success(message="Founder deleted")
