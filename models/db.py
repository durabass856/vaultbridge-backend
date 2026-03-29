import pymysql
import os
from flask import jsonify

# =========================
# DB CONNECTION
# =========================
def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        cursorclass=pymysql.cursors.DictCursor
    )

# =========================
# QUERY FUNCTION (UPDATED)
# =========================
def query(sql, args=None, fetch="all"):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(sql, args or ())

        if fetch == "all":
            data = cur.fetchall()
        elif fetch == "one":
            data = cur.fetchone()
        else:
            conn.commit()
            data = {
                "affected_rows": cur.rowcount,
                "lastrowid": cur.lastrowid
            }

        cur.close()
        conn.close()

        return data, None

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, str(e)

# =========================
# RESPONSE HELPERS (UNCHANGED)
# =========================
def success(data=None, message="ok", status=200):
    return jsonify({
        "success": True,
        "message": message,
        "data": data
    }), status


def error(message="An error occurred", status=400):
    return jsonify({
        "success": False,
        "message": message
    }), status
