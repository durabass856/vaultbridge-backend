from flask import Blueprint, request
from models.db import query, success, error

portfolio_bp = Blueprint("portfolio", __name__)

@portfolio_bp.route("/", methods=["GET"])
def get_portfolio():
    sql = """SELECT ip.*,
                    CONCAT(sh.first_name,' ',sh.last_name) AS shark_name,
                    s.startup_name
             FROM investment_portfolio ip
             JOIN shark sh ON ip.shark_id=sh.shark_id
             JOIN startup s ON ip.startup_id=s.startup_id
             ORDER BY ip.portfolio_id DESC"""
    data, err = query(sql)
    return success(data) if not err else error(err)

@portfolio_bp.route("/", methods=["POST"])
def create_portfolio():
    b = request.get_json()
    if not b.get("shark_id") or not b.get("startup_id"): return error("shark_id and startup_id required")
    sql = """INSERT INTO investment_portfolio
             (shark_id,startup_id,total_invested_usd,current_equity_percent,
              portfolio_status,first_investment_date,current_valuation_usd,roi_percent)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""
    data, err = query(sql,(b["shark_id"],b["startup_id"],b.get("total_invested_usd"),
                           b.get("current_equity_percent"),b.get("portfolio_status","Active"),
                           b.get("first_investment_date"),b.get("current_valuation_usd"),
                           b.get("roi_percent")),fetch="none")
    return (success({"portfolio_id":data["lastrowid"]},"Portfolio entry created",201) if not err else error(err))

@portfolio_bp.route("/<int:pid>", methods=["PUT"])
def update_portfolio(pid):
    b = request.get_json()
    sql = """UPDATE investment_portfolio SET total_invested_usd=%s,current_equity_percent=%s,
             portfolio_status=%s,current_valuation_usd=%s,roi_percent=%s WHERE portfolio_id=%s"""
    data, err = query(sql,(b.get("total_invested_usd"),b.get("current_equity_percent"),
                           b.get("portfolio_status"),b.get("current_valuation_usd"),
                           b.get("roi_percent"),pid),fetch="none")
    return success(message="Portfolio updated") if not err else error(err)

@portfolio_bp.route("/<int:pid>", methods=["DELETE"])
def delete_portfolio(pid):
    data, err = query("DELETE FROM investment_portfolio WHERE portfolio_id=%s",(pid,),fetch="none")
    return success(message="Portfolio entry deleted") if not err else error(err)
