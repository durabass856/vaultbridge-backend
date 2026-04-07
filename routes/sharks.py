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
        # ── 1. VALIDATION ──────────────────────────────────────────────
        if not b or not b.get("first_name"):
            return error("first_name is required")

        # ── 2. INSERT SHARK ────────────────────────────────────────────
        cur.execute("""
            INSERT INTO shark
            (first_name, last_name, email, phone, date_of_birth, nationality,
             net_worth_usd_millions, bio)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            b.get("first_name"),
            b.get("last_name"),
            b.get("email"),
            b.get("phone"),
            b.get("date_of_birth") or None,
            b.get("nationality"),
            b.get("net_worth_usd_millions"),
            b.get("bio"),
        ))

        shark_id = cur.lastrowid

        # ── 3. COMPANY (optional) ──────────────────────────────────────
        # FIX: include website, aum_usd_millions, city, country columns
        # that were missing and causing the 500 error when a company name
        # was provided.
        c = b.get("company")
        if c and c.get("company_name"):
            cur.execute("""
                INSERT INTO investor_company
                    (company_name, company_type, website,
                     aum_usd_millions, city, country)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                c.get("company_name"),
                c.get("company_type") or None,
                c.get("website") or None,
                float(c["aum"]) if c.get("aum") else None,
                c.get("city") or None,
                c.get("country") or None,
            ))

            company_id = cur.lastrowid
            cur.execute(
                "UPDATE shark SET company_id=%s WHERE shark_id=%s",
                (company_id, shark_id)
            )

        # ── 4. EXPERTISE ───────────────────────────────────────────────
        # FIX: also insert years_experience which was being silently
        # dropped before, and support both array and flat fallback.
        expertise_list = b.get("expertise", [])
        if not expertise_list and b.get("expertise_domain"):
            expertise_list = [{
                "domain": b["expertise_domain"],
                "years_experience": None,
                "is_primary": 1,
            }]

        for i, e in enumerate(expertise_list):
            if not e.get("domain"):
                continue  # skip empty entries

            # frontend sends `years` or `years_experience`
            years = e.get("years_experience") or e.get("years") or None
            try:
                years = int(years) if years is not None else None
            except (ValueError, TypeError):
                years = None

            cur.execute("""
                INSERT INTO shark_expertise
                    (shark_id, domain, years_experience, is_primary)
                VALUES (%s, %s, %s, %s)
            """, (
                shark_id,
                e.get("domain"),
                years,
                1 if i == 0 else int(bool(e.get("is_primary", 0))),
            ))

        # ── 5. PORTFOLIO ───────────────────────────────────────────────
        for p in b.get("portfolio", []):
            if not p.get("startup_id"):
                continue
            cur.execute("""
                INSERT INTO investment_portfolio
                    (shark_id, startup_id, total_invested_usd,
                     current_equity_percent, portfolio_status,
                     current_valuation_usd, roi_percent)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                shark_id,
                p.get("startup_id"),
                p.get("total_invested_usd"),
                p.get("current_equity_percent"),
                p.get("portfolio_status", "Active"),
                p.get("current_valuation_usd"),
                p.get("roi_percent"),
            ))

        # ── 6. DEAL (optional) ─────────────────────────────────────────
        # FIX: was missing deal_notes in the INSERT and was not inserting
        # into the deal_shark junction table (contribution, equity_share,
        # is_lead_investor).
        d = b.get("deal")
        if d and d.get("startup_id"):
            cur.execute("""
                INSERT INTO deal
                    (startup_id, deal_amount_usd, deal_equity_percent,
                     deal_type, handshake_date, deal_status, deal_notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                d.get("startup_id"),
                d.get("deal_amount_usd"),
                d.get("deal_equity_percent"),
                d.get("deal_type", "Equity"),
                d.get("handshake_date") or None,
                d.get("deal_status", "Handshake"),
                d.get("deal_notes") or None,
            ))

            deal_id = cur.lastrowid

            # Insert the investor's participation in the deal
            for shark_entry in d.get("sharks", []):
                entry_shark_id = shark_entry.get("shark_id") or shark_id
                cur.execute("""
                    INSERT INTO deal_shark
                        (deal_id, shark_id, contribution_usd,
                         equity_share_percent, is_lead_investor)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    deal_id,
                    entry_shark_id,
                    shark_entry.get("contribution") or None,
                    shark_entry.get("equity") or None,
                    int(bool(shark_entry.get("is_lead", 0))),
                ))

            # If no explicit sharks array, still link the current shark
            if not d.get("sharks"):
                cur.execute("""
                    INSERT INTO deal_shark
                        (deal_id, shark_id, is_lead_investor)
                    VALUES (%s, %s, %s)
                """, (deal_id, shark_id, 0))

        conn.commit()
        return success({"shark_id": shark_id}, "Investor created", 201)

    except Exception as e:
        conn.rollback()
        return error(str(e), 500)

    finally:
        cur.close()
        conn.close()


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
