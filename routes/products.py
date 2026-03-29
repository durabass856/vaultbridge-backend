from flask import Blueprint, request
from models.db import query, success, error

products_bp = Blueprint("products", __name__)

@products_bp.route("/", methods=["GET"])
def get_products():
    sql = """SELECT p.*, s.startup_name, pc.category_name
             FROM product p
             LEFT JOIN startup s ON p.startup_id=s.startup_id
             LEFT JOIN product_category pc ON p.category_id=pc.category_id
             ORDER BY p.product_id DESC"""
    data, err = query(sql)
    return success(data) if not err else error(err)

@products_bp.route("/", methods=["POST"])
def create_product():
    b = request.get_json()
    if not b.get("startup_id") or not b.get("product_name"): return error("startup_id and product_name required")
    sql = """INSERT INTO product (startup_id,category_id,product_name,description,
             unit_price_usd,launch_date,is_patented,units_sold) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""
    data, err = query(sql,(b["startup_id"],b.get("category_id"),b["product_name"],
                           b.get("description"),b.get("unit_price_usd"),b.get("launch_date"),
                           b.get("is_patented",0),b.get("units_sold")),fetch="none")
    return (success({"product_id":data["lastrowid"]},"Product created",201) if not err else error(err))

@products_bp.route("/<int:pid>", methods=["PUT"])
def update_product(pid):
    b = request.get_json()
    sql = """UPDATE product SET startup_id=%s,category_id=%s,product_name=%s,description=%s,
             unit_price_usd=%s,launch_date=%s,is_patented=%s,units_sold=%s WHERE product_id=%s"""
    data, err = query(sql,(b.get("startup_id"),b.get("category_id"),b.get("product_name"),
                           b.get("description"),b.get("unit_price_usd"),b.get("launch_date"),
                           b.get("is_patented"),b.get("units_sold"),pid),fetch="none")
    return success(message="Product updated") if not err else error(err)

@products_bp.route("/<int:pid>", methods=["DELETE"])
def delete_product(pid):
    data, err = query("DELETE FROM product WHERE product_id=%s",(pid,),fetch="none")
    return success(message="Product deleted") if not err else error(err)
