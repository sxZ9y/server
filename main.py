from flask import Flask, request, jsonify
import psycopg2
import os
import time
import random
import string
from urllib.parse import urlparse

app = Flask(__name__)

# -------------------------
# DATABASE
# -------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    url = urlparse(DATABASE_URL)
    return psycopg2.connect(
        dbname=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port,
        sslmode="require"
    )

def init_db():
    with get_db() as conn:
        with conn.cursor() as c:
            c.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                id SERIAL PRIMARY KEY,
                ip TEXT UNIQUE,
                order_id TEXT,
                license_key TEXT,
                created_at BIGINT
            )
            """)
        conn.commit()

init_db()

# -------------------------
# LICENSE GENERATOR
# -------------------------
class NewLicenseGenerator:
    def __init__(self, seed=None):
        random.seed(seed)

    def generate_license_key(self):
        block1 = f"AFX{random.randint(0,9)}9{random.randint(0,9)}7"
        block2 = f"{random.randint(0,9)}0{random.choice(string.ascii_uppercase)}0{random.choice(string.ascii_uppercase)}9"
        block3 = f"{random.randint(0,9)}{random.choice(string.ascii_uppercase)}{random.randint(0,9)}7"
        block4 = "DR9C7"
        block5 = "090909"
        block6 = f"{random.randint(0,9)}{random.choice(string.ascii_uppercase)}{random.randint(0,9)}{random.choice(string.ascii_uppercase)}{random.randint(0,9)}8"
        block7 = f"{random.randint(0,9)}{random.randint(0,9)}{random.randint(0,9)}7"
        block8 = f"{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}6"
        block9 = "9"
        block10 = "0000"
        return f"{block1}{block2}{block3}{block4}{block5}{block6}{block7}{block8}{block9}{block10}"

generator = NewLicenseGenerator()

# -------------------------
# ROUTE: GET LICENSE
# -------------------------
@app.route("/get-license", methods=["POST"])
def get_license():
    try:
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        data = request.json or {}
        order_id = data.get("order_id")

        if not order_id:
            return jsonify({
                "error": "Order ID is required",
                "contact": "discord: rubikskubiks12"
            }), 400

        with get_db() as conn:
            with conn.cursor() as c:

                # ONE LICENSE PER IP
                c.execute(
                    "SELECT license_key FROM licenses WHERE ip = %s",
                    (ip,)
                )
                row = c.fetchone()
                if row:
                    return jsonify({
                        "message": "You have already received your license",
                        "license": row[0]
                    })

                license_key = generator.generate_license_key()

                c.execute("""
                    INSERT INTO licenses (ip, order_id, license_key, created_at)
                    VALUES (%s, %s, %s, %s)
                """, (ip, order_id, license_key, int(time.time())))
                conn.commit()

        return jsonify({
            "success": True,
            "license": license_key
        })

    except Exception:
        return jsonify({
            "error": "A system error occurred",
            "contact": "discord: rubikskubiks12"
        }), 500


# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

