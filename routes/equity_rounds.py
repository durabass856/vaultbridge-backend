from flask import Blueprint, request
from models.db import query, success, error

equity_bp = Blueprint("equity_rounds", __name__)

@equity_bp.route("/", methods=["GET"])
def get_equity():
    sql = """SELECT er.*, s.startup_name FROM equity_round er
             JOIN startup s ON er.startup_id=s.startup_id ORDER BY er.round_date DESC"""
    data, err = query(sql)
    return success(data) if not err else error(err)

@equity_bp.route("/", methods=["POST"])
def create_equity():
    b = request.get_json()
    sql = """INSERT INTO equity_round
             (startup_id,deal_id,round_type,round_date,amount_raised_usd,
              pre_money_valuation_usd,post_money_valuation_usd,lead_investor_name,num_investors_in_round)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    data, err = query(sql,(b.get("startup_id"),b.get("deal_id"),b.get("round_type"),
                           b.get("round_date"),b.get("amount_raised_usd"),
                           b.get("pre_money_valuation_usd"),b.get("post_money_valuation_usd"),
                           b.get("lead_investor_name"),b.get("num_investors_in_round",1)),fetch="none")
    return (success({"round_id":data["lastrowid"]},"Equity round added",201) if not err else error(err))

@equity_bp.route("/<int:rid>", methods=["DELETE"])
def delete_equity(rid):
    data, err = query("DELETE FROM equity_round WHERE round_id=%s",(rid,),fetch="none")
    return success(message="Equity round deleted") if not err else error(err)
