from flask import Blueprint, request
from models.db import query, success, error

milestones_bp = Blueprint("milestones", __name__)

@milestones_bp.route("/", methods=["GET"])
def get_milestones():
    sql = """SELECT m.*, s.startup_name FROM milestone m
             JOIN startup s ON m.startup_id=s.startup_id ORDER BY m.milestone_date DESC"""
    data, err = query(sql)
    return success(data) if not err else error(err)

@milestones_bp.route("/", methods=["POST"])
def create_milestone():
    b = request.get_json()
    if not b.get("startup_id"): return error("startup_id required")
    sql = """INSERT INTO milestone (startup_id,deal_id,milestone_date,milestone_type,description,verified)
             VALUES (%s,%s,%s,%s,%s,%s)"""
    data, err = query(sql,(b["startup_id"],b.get("deal_id"),b.get("milestone_date"),
                           b.get("milestone_type"),b.get("description"),b.get("verified",0)),fetch="none")
    return (success({"milestone_id":data["lastrowid"]},"Milestone created",201) if not err else error(err))

@milestones_bp.route("/<int:mid>", methods=["PUT"])
def update_milestone(mid):
    b = request.get_json()
    sql = """UPDATE milestone SET milestone_date=%s,milestone_type=%s,description=%s,verified=%s
             WHERE milestone_id=%s"""
    data, err = query(sql,(b.get("milestone_date"),b.get("milestone_type"),
                           b.get("description"),b.get("verified"),mid),fetch="none")
    return success(message="Milestone updated") if not err else error(err)

@milestones_bp.route("/<int:mid>", methods=["DELETE"])
def delete_milestone(mid):
    data, err = query("DELETE FROM milestone WHERE milestone_id=%s",(mid,),fetch="none")
    return success(message="Milestone deleted") if not err else error(err)
