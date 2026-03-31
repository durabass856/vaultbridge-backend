from flask import Flask, g
from flask_cors import CORS
import pymysql
import pymysql.cursors
import os

def get_db():
    if 'db' not in g:
        g.db = pymysql.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DB"),
            port=int(os.getenv("MYSQL_PORT", 3306)),
            cursorclass=pymysql.cursors.DictCursor
        )
    return g.db

def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.teardown_appcontext
    def close_db(error):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    from routes.startups import startups_bp
    from routes.founders import founders_bp
    from routes.sharks import sharks_bp
    from routes.deals import deals_bp
    from routes.products import products_bp
    from routes.portfolio import portfolio_bp
    from routes.metrics import metrics_bp
    from routes.milestones import milestones_bp
    from routes.due_diligence import dd_bp
    from routes.valuations import valuations_bp
    from routes.health_scores import health_bp
    from routes.team_history import team_bp
    from routes.equity_rounds import equity_bp
    from routes.locations import locations_bp
    from routes.industries import industries_bp
    from routes.product_categories import product_categories_bp

    

    app.register_blueprint(startups_bp, url_prefix="/api/startups")
    app.register_blueprint(founders_bp, url_prefix="/api/founders")
    app.register_blueprint(sharks_bp, url_prefix="/api/sharks")
    app.register_blueprint(deals_bp, url_prefix="/api/deals")
    app.register_blueprint(products_bp, url_prefix="/api/products")
    app.register_blueprint(portfolio_bp, url_prefix="/api/portfolio")
    app.register_blueprint(metrics_bp, url_prefix="/api/metrics")
    app.register_blueprint(milestones_bp, url_prefix="/api/milestones")
    app.register_blueprint(dd_bp, url_prefix="/api/due-diligence")
    app.register_blueprint(valuations_bp, url_prefix="/api/valuations")
    app.register_blueprint(health_bp, url_prefix="/api/health-scores")
    app.register_blueprint(team_bp, url_prefix="/api/team-history")
    app.register_blueprint(equity_bp, url_prefix="/api/equity-rounds")
    app.register_blueprint(locations_bp, url_prefix="/api/locations")
    app.register_blueprint(industries_bp, url_prefix="/api/industries")
    app.register_blueprint(product_categories_bp, url_prefix="/api/product-categories")

    @app.route("/api/health")
    def health_check():
        return {"status": "ok", "message": "TankTrack API running"}

    return app

if __name__ == "__main__":
    app = create_app()
    PORT = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=PORT)

pymysql
