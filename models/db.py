from app import mysql
from flask import jsonify

def query(sql, args=None, fetch="all"):
    try:
        cur = mysql.connection.cursor()
        cur.execute(sql, args or ())
        if fetch == "all":
            data = cur.fetchall()
        elif fetch == "one":
            data = cur.fetchone()
        else:
            mysql.connection.commit()
            data = {"affected_rows": cur.rowcount, "lastrowid": cur.lastrowid}
        cur.close()
        return data, None
    except Exception as e:
        import traceback
        traceback.print_exc()        # ← prints full error in Flask terminal
        return None, str(e)

def success(data=None, message="ok", status=200):
    return jsonify({"success": True, "message": message, "data": data}), status

def error(message="An error occurred", status=400):
    return jsonify({"success": False, "message": message}), status