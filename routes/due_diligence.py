from flask import Blueprint, request
from models.db import query, success, error

dd_bp = Blueprint("due_diligence", __name__)

@dd_bp.route("/", methods=["GET"])
def get_dd():
    sql = """SELECT dd.*, d.startup_id, s.startup_name FROM due_diligence dd
             JOIN deal d ON dd.deal_id=d.deal_id
             JOIN startup s ON d.startup_id=s.startup_id ORDER BY dd.initiated_date DESC"""
    data, err = query(sql)
    return success(data) if not err else error(err)

@dd_bp.route("/", methods=["POST"])
def create_dd():
    b = request.get_json()
    if not b.get("deal_id"): return error("deal_id required")
    sql = """INSERT INTO due_diligence
             (deal_id,initiated_date,completed_date,dd_status,conducted_by,
              financial_verified,legal_cleared,ip_verified,notes)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    data, err = query(sql,(b["deal_id"],b.get("initiated_date"),b.get("completed_date"),
                           b.get("dd_status","Ongoing"),b.get("conducted_by"),
                           b.get("financial_verified",0),b.get("legal_cleared",0),
                           b.get("ip_verified",0),b.get("notes")),fetch="none")
    return (success({"dd_id":data["lastrowid"]},"DD record created",201) if not err else error(err))

@dd_bp.route("/<int:did>", methods=["PUT"])
def update_dd(did):
    b = request.get_json()
    sql = """UPDATE due_diligence SET completed_date=%s,dd_status=%s,conducted_by=%s,
             financial_verified=%s,legal_cleared=%s,ip_verified=%s,notes=%s WHERE dd_id=%s"""
    data, err = query(sql,(b.get("completed_date"),b.get("dd_status"),b.get("conducted_by"),
                           b.get("financial_verified"),b.get("legal_cleared"),
                           b.get("ip_verified"),b.get("notes"),did),fetch="none")
    return success(message="DD updated") if not err else error(err)

@dd_bp.route("/<int:did>", methods=["DELETE"])
def delete_dd(did):
    data, err = query("DELETE FROM due_diligence WHERE dd_id=%s",(did,),fetch="none")
    return success(message="DD record deleted") if not err else error(err)
