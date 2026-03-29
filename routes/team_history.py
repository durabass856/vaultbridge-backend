from flask import Blueprint, request
from models.db import query, success, error

team_bp = Blueprint("team_history", __name__)

@team_bp.route("/", methods=["GET"])
def get_team():
    sql = """SELECT t.*, s.startup_name FROM startup_team_history t
             JOIN startup s ON t.startup_id=s.startup_id ORDER BY t.record_date DESC"""
    data, err = query(sql)
    return success(data) if not err else error(err)

@team_bp.route("/", methods=["POST"])
def create_team():
    b = request.get_json()
    sql = """INSERT INTO startup_team_history
             (startup_id,record_date,total_headcount,engineering_count,
              sales_count,ops_count,change_type,change_count,notes)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    data, err = query(sql,(b.get("startup_id"),b.get("record_date"),b.get("total_headcount"),
                           b.get("engineering_count"),b.get("sales_count"),b.get("ops_count"),
                           b.get("change_type"),b.get("change_count"),b.get("notes")),fetch="none")
    return (success({"team_id":data["lastrowid"]},"Team record added",201) if not err else error(err))

@team_bp.route("/<int:tid>", methods=["DELETE"])
def delete_team(tid):
    data, err = query("DELETE FROM startup_team_history WHERE team_id=%s",(tid,),fetch="none")
    return success(message="Team record deleted") if not err else error(err)
