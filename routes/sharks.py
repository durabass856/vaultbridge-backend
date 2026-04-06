from flask import Blueprint, request
from models.db import get_connection, query, success, error

sharks_bp = Blueprint("sharks", __name__)

# ─────────────────────────────────────────────
# GET ALL SHARKS
# ─────────────────────────────────────────────
@sharks_bp.route("/", methods=["GET"])
def get_all():
    sql = """
        SELECT 
            sh.*, 
            ic.company_name, 
            ic.company_type,

            -- 🔥 NEW
            fn_total_invested_by_shark(sh.shark_id) AS total_invested_usd

        FROM shark sh
        LEFT JOIN investor_company ic ON sh.company_id = ic.company_id
        ORDER BY sh.shark_id DESC
    """
    data, err = query(sql)
    return success(data) if not err else error(err)


# ─────────────────────────────────────────────
# GET ONE SHARK
# ─────────────────────────────────────────────
@sharks_bp.route("/<int:sid>", methods=["GET"])
def get_one(sid):
    shark, err = query(
        """
        SELECT 
            sh.*, 
            fn_total_invested_by_shark(sh.shark_id) AS total_invested_usd
        FROM shark sh
        WHERE sh.shark_id = %s
        """,
        (sid,), fetch="one"
    )

    if err: return error(err)
    if not shark: return error("Shark not found", 404)

    expertise, _ = query("SELECT * FROM shark_expertise WHERE shark_id=%s", (sid,))
    shark["expertise"] = expertise or []

    return success(shark)


# ─────────────────────────────────────────────
# PORTFOLIO SUMMARY (🔥 IMPORTANT)
# ─────────────────────────────────────────────
@sharks_bp.route("/<int:sid>/portfolio-summary", methods=["GET"])
def get_portfolio_summary(sid):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("CALL sp_investor_portfolio_summary(%s)", (sid,))

        summary = cur.fetchone()

        cur.nextset()
        items = cur.fetchall()

        while cur.nextset():
            pass

        cur.close()
        conn.close()

        return success({
            "summary": summary or {},
            "portfolio_items": items or []
        })

    except Exception as exc:
        return error(str(exc), 500)


# ─────────────────────────────────────────────
# CREATE SHARK
# ─────────────────────────────────────────────
@sharks_bp.route("/", methods=["POST"])
def create():
    b = request.get_json()

    if not b or not b.get("first_name"):
        return error("first_name is required")

    sql = """
        INSERT INTO shark
        (first_name,last_name,email,phone,date_of_birth,nationality,
         net_worth_usd_millions,company_id,bio)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    args = (
        b.get("first_name"),
        b.get("last_name"),
        b.get("email"),
        b.get("phone"),
        b.get("date_of_birth"),
        b.get("nationality"),
        b.get("net_worth_usd_millions"),
        b.get("company_id"),
        b.get("bio")
    )

    data, err = query(sql, args, fetch="none")
    if err: return error(err)

    sid = data["lastrowid"]

    if b.get("expertise_domain"):
        query(
            "INSERT INTO shark_expertise (shark_id,domain,is_primary) VALUES (%s,%s,1)",
            (sid, b["expertise_domain"]),
            fetch="none"
        )

    return success({"shark_id": sid}, "Investor created", 201)


# ─────────────────────────────────────────────
# UPDATE SHARK
# ─────────────────────────────────────────────
@sharks_bp.route("/<int:sid>", methods=["PUT"])
def update(sid):
    b = request.get_json()

    sql = """
        UPDATE shark SET 
            first_name=%s,
            last_name=%s,
            email=%s,
            phone=%s,
            nationality=%s,
            net_worth_usd_millions=%s,
            company_id=%s,
            bio=%s
        WHERE shark_id=%s
    """

    args = (
        b.get("first_name"),
        b.get("last_name"),
        b.get("email"),
        b.get("phone"),
        b.get("nationality"),
        b.get("net_worth_usd_millions"),
        b.get("company_id"),
        b.get("bio"),
        sid
    )

    data, err = query(sql, args, fetch="none")
    if err: return error(err)

    return success(message="Investor updated")


# ─────────────────────────────────────────────
# DELETE SHARK
# ─────────────────────────────────────────────
@sharks_bp.route("/<int:sid>", methods=["DELETE"])
def delete(sid):
    data, err = query("DELETE FROM shark WHERE shark_id=%s", (sid,), fetch="none")
    if err: return error(err)

    return success(message="Investor deleted")
