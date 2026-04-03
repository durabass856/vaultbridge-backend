from flask import Blueprint, request
from app import mysql
from models.db import query, success, error

startups_bp = Blueprint("startups", __name__)


def ensure_db_lab_objects():
    cur = mysql.connection.cursor()
    try:
        cur.execute("DROP TRIGGER IF EXISTS trg_startup_status_history")
        cur.execute(
            """
            CREATE TRIGGER trg_startup_status_history
            AFTER UPDATE ON startup
            FOR EACH ROW
            BEGIN
                IF NOT (OLD.status <=> NEW.status) THEN
                    INSERT INTO startup_status_history (
                        startup_id,
                        previous_status,
                        new_status,
                        changed_date,
                        changed_by,
                        reason,
                        verified
                    )
                    VALUES (
                        NEW.startup_id,
                        OLD.status,
                        NEW.status,
                        CURDATE(),
                        'VaultBridge trigger',
                        CONCAT('Status changed automatically from ', OLD.status, ' to ', NEW.status),
                        1
                    );
                END IF;
            END
            """
        )

        cur.execute("DROP PROCEDURE IF EXISTS sp_cursor_startup_metric_summary")
        cur.execute(
            """
            CREATE PROCEDURE sp_cursor_startup_metric_summary(IN p_startup_id INT)
            BEGIN
                DECLARE done INT DEFAULT 0;
                DECLARE v_revenue DECIMAL(14,2) DEFAULT 0;
                DECLARE v_burn DECIMAL(14,2) DEFAULT 0;
                DECLARE v_runway DECIMAL(10,2) DEFAULT 0;
                DECLARE v_customers INT DEFAULT 0;
                DECLARE snapshot_count INT DEFAULT 0;
                DECLARE total_revenue DECIMAL(18,2) DEFAULT 0;
                DECLARE total_burn DECIMAL(18,2) DEFAULT 0;
                DECLARE total_runway DECIMAL(18,2) DEFAULT 0;
                DECLARE latest_customers INT DEFAULT 0;

                DECLARE metrics_cursor CURSOR FOR
                    SELECT
                        COALESCE(monthly_revenue_usd, 0),
                        COALESCE(monthly_burn_usd, 0),
                        COALESCE(runway_months, 0),
                        COALESCE(customer_count, 0)
                    FROM startup_operational_metrics
                    WHERE startup_id = p_startup_id
                    ORDER BY snapshot_date;

                DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

                OPEN metrics_cursor;

                read_loop: LOOP
                    FETCH metrics_cursor INTO v_revenue, v_burn, v_runway, v_customers;
                    IF done = 1 THEN
                        LEAVE read_loop;
                    END IF;

                    SET snapshot_count = snapshot_count + 1;
                    SET total_revenue = total_revenue + v_revenue;
                    SET total_burn = total_burn + v_burn;
                    SET total_runway = total_runway + v_runway;
                    SET latest_customers = v_customers;
                END LOOP;

                CLOSE metrics_cursor;

                SELECT
                    p_startup_id AS startup_id,
                    snapshot_count AS snapshots_processed,
                    total_revenue AS total_revenue_usd,
                    total_burn AS total_burn_usd,
                    ROUND(IF(snapshot_count = 0, 0, total_runway / snapshot_count), 2) AS average_runway_months,
                    latest_customers AS latest_customer_count;
            END
            """
        )

        mysql.connection.commit()
        return None
    finally:
        cur.close()


# GET /api/startups
@startups_bp.route("/", methods=["GET"])
def get_all():
    sql = """
        SELECT s.*,
               i.industry_name,
               CONCAT(l.city, ', ', l.country) AS location_display
        FROM startup s
        LEFT JOIN industry i ON s.industry_id = i.industry_id
        LEFT JOIN location l ON s.location_id = l.location_id
        ORDER BY s.created_at DESC
    """
    data, err = query(sql)
    if err: return error(err)
    return success(data)


# GET /api/startups/<id>
@startups_bp.route("/<int:sid>", methods=["GET"])
def get_one(sid):
    sql = """
        SELECT s.*,
               i.industry_name,
               CONCAT(l.city, ', ', l.country) AS location_display
        FROM startup s
        LEFT JOIN industry i ON s.industry_id = i.industry_id
        LEFT JOIN location l ON s.location_id = l.location_id
        WHERE s.startup_id = %s
    """
    data, err = query(sql, (sid,), fetch="one")
    if err: return error(err)
    if not data: return error("Startup not found", 404)
    return success(data)


@startups_bp.route("/db-lab/setup", methods=["POST"])
def setup_db_lab():
    try:
        ensure_db_lab_objects()
        return success(
            {
                "trigger": "trg_startup_status_history",
                "procedure": "sp_cursor_startup_metric_summary",
            },
            "Trigger and cursor procedure are ready",
        )
    except Exception as exc:
        return error(str(exc), 500)


@startups_bp.route("/<int:sid>/status-history", methods=["GET"])
def get_status_history(sid):
    sql = """
        SELECT *
        FROM startup_status_history
        WHERE startup_id = %s
        ORDER BY changed_date DESC, status_history_id DESC
    """
    data, err = query(sql, (sid,))
    if err:
        return error(err)
    return success(data)


@startups_bp.route("/<int:sid>/cursor-summary", methods=["GET"])
def get_cursor_summary(sid):
    try:
        ensure_db_lab_objects()
        cur = mysql.connection.cursor()
        cur.execute("CALL sp_cursor_startup_metric_summary(%s)", (sid,))
        data = cur.fetchone()
        while cur.nextset():
            pass
        cur.close()
        return success(data or {})
    except Exception as exc:
        return error(str(exc), 500)


# POST /api/startups
@startups_bp.route("/", methods=["POST"])
def create():
    b = request.get_json()
    required = ["startup_name", "founded_year"]
    for f in required:
        if not b.get(f): return error(f"{f} is required")

    sql = """
        INSERT INTO startup
          (startup_name, tagline, industry_id, location_id, website,
           founded_year, registration_number, annual_revenue_usd,
           profit_loss_usd, num_employees, total_funding_usd, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    args = (
        b.get("startup_name"), b.get("tagline"),
        b.get("industry_id"), b.get("location_id"),
        b.get("website"), b.get("founded_year"),
        b.get("registration_number"), b.get("annual_revenue_usd"),
        b.get("profit_loss_usd"), b.get("num_employees"),
        b.get("total_funding_usd", 0), b.get("status", "Active"),
    )
    data, err = query(sql, args, fetch="none")
    if err: return error(err)
    return success({"startup_id": data["lastrowid"]}, "Startup created", 201)


# PUT /api/startups/<id>
@startups_bp.route("/<int:sid>", methods=["PUT"])
def update(sid):
    b = request.get_json()
    sql = """
        UPDATE startup SET
          startup_name=%s, tagline=%s, industry_id=%s, location_id=%s,
          website=%s, founded_year=%s, registration_number=%s,
          annual_revenue_usd=%s, profit_loss_usd=%s, num_employees=%s,
          total_funding_usd=%s, status=%s
        WHERE startup_id=%s
    """
    args = (
        b.get("startup_name"), b.get("tagline"),
        b.get("industry_id"), b.get("location_id"),
        b.get("website"), b.get("founded_year"),
        b.get("registration_number"), b.get("annual_revenue_usd"),
        b.get("profit_loss_usd"), b.get("num_employees"),
        b.get("total_funding_usd"), b.get("status"), sid,
    )
    data, err = query(sql, args, fetch="none")
    if err: return error(err)
    return success(message="Startup updated")


# DELETE /api/startups/<id>
@startups_bp.route("/<int:sid>", methods=["DELETE"])
def delete(sid):
    data, err = query("DELETE FROM startup WHERE startup_id=%s", (sid,), fetch="none")
    if err: return error(err)
    return success(message="Startup deleted")
