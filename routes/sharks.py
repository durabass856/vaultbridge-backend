from flask import Blueprint, request
from models.db import query, success, error

sharks_bp = Blueprint("sharks", __name__)

@sharks_bp.route("/", methods=["GET"])
def get_all():
    sql = """
        SELECT sh.*, ic.company_name, ic.company_type
        FROM shark sh
        LEFT JOIN investor_company ic ON sh.company_id = ic.company_id
        ORDER BY sh.shark_id DESC
    """
    data, err = query(sql)
    return success(data) if not err else error(err)

@sharks_bp.route("/<int:sid>", methods=["GET"])
def get_one(sid):
    shark, err = query("SELECT * FROM shark WHERE shark_id=%s", (sid,), fetch="one")

    if err: return error(err)
    if not shark: return error("Shark not found", 404)

    expertise, _ = query("SELECT * FROM shark_expertise WHERE shark_id=%s", (sid,))
    shark["expertise"] = expertise or []

    return success(shark)
