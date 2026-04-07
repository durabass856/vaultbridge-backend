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
# PORTFOLIO SUMMARY
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
    conn = get_connection()
    cur = conn.cursor()

    try:
        # 🔹 1. VALIDATION
        if not b or not b.get("first_name"):
            return error("first_name is required")

        # 🔹 2. INSERT SHARK
        cur.execute("""
            INSERT INTO shark
            (first_name,last_name,email,phone,date_of_birth,nationality,
             net_worth_usd_millions,bio)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            b.get("first_name"),
            b.get("last_name"),
            b.get("email"),
            b.get("phone"),
            b.get("date_of_birth"),
            b.get("nationality"),
            b.get("net_worth_usd_millions"),
            b.get("bio")
        ))

        shark_id = cur.lastrowid

        # 🔹 3. COMPANY (optional)
        if b.get("company"):
            c = b["company"]

            cur.execute("""
                INSERT INTO investor_company (company_name, company_type)
                VALUES (%s,%s)
            """, (
                c.get("company_name"),
                c.get("company_type")
            ))

            company_id = cur.lastrowid

            cur.execute(
                "UPDATE shark SET company_id=%s WHERE shark_id=%s",
                (company_id, shark_id)
            )

        # 🔹 4. EXPERTISE
        # ✅ FIX: support both array format and flat expertise_domain fallback
        expertise_list = b.get("expertise", [])
        if not expertise_list and b.get("expertise_domain"):
            expertise_list = [{"domain": b["expertise_domain"], "is_primary": 1}]

        for e in expertise_list:
            if not e.get("domain"):
                continue  # skip empty entries
            cur.execute("""
                INSERT INTO shark_expertise (shark_id,domain,is_primary)
                VALUES (%s,%s,%s)
            """, (
                shark_id,
                e.get("domain"),
                e.get("is_primary", 1)
            ))

        # 🔹 5. PORTFOLIO
        for p in b.get("portfolio", []):
            cur.execute("""
                INSERT INTO investment_portfolio
                (shark_id,startup_id,total_invested_usd,current_equity_percent,
                 portfolio_status,current_valuation_usd,roi_percent)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (
                shark_id,
                p.get("startup_id"),
                p.get("total_invested_usd"),
                p.get("current_equity_percent"),
                p.get("portfolio_status", "Active"),
                p.get("current_valuation_usd"),
                p.get("roi_percent")
            ))

        # 🔹 6. DEAL (optional)
        if b.get("deal"):
            d = b["deal"]

            cur.execute("""
                INSERT INTO deal
                (startup_id,deal_amount_usd,deal_equity_percent,
                 deal_type,handshake_date,deal_status)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                d.get("startup_id"),
                d.get("deal_amount_usd"),
                d.get("deal_equity_percent"),
                d.get("deal_type", "Equity"),
                d.get("handshake_date"),
                d.get("deal_status", "Handshake")
            ))

        conn.commit()
        return success({"shark_id": shark_id}, "Investor created", 201)

    except Exception as e:
        conn.rollback()
        return error(str(e), 500)


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
