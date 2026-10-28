"""
server.py — Flask + SQLite

A separate web server and product database API
"""
from flask import Flask, jsonify, request, send_from_directory
from pathlib import Path
import json
import sqlite3
import os
import re
import io

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Render charts without a desktop display.
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("VELOCART_DB_PATH", BASE_DIR / "velocart.db"))
SEED_PATH = BASE_DIR / "products_seed.json"

app = Flask(__name__, static_folder=None)

def get_db():
    connection = sqlite3.connect(DB_PATH, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    return connection

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL CHECK(price > 0),
                cost REAL NOT NULL DEFAULT 0 CHECK(cost >= 0),
                sold INTEGER NOT NULL DEFAULT 0 CHECK(sold >= 0),
                stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
                image TEXT NOT NULL DEFAULT 'assets/product-photos/water-bottle.jpg',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        count = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count == 0 and SEED_PATH.exists():
            seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
            db.executemany("""
                INSERT INTO products (id, name, category, price, cost, sold, stock, image)
                VALUES (:id, :name, :category, :price, :cost, :sold, :stock, :image)
            """, seed)

def row_to_product(row):
    return {
        "id": row["id"], "name": row["name"], "category": row["category"],
        "price": row["price"], "cost": row["cost"], "sold": row["sold"],
        "stock": row["stock"], "image": row["image"]
    }

@app.get("/")
def home():
    return send_from_directory(BASE_DIR, "landing.html")

@app.get("/<path:filename>")
def static_files(filename):
    # Only serve files that actually exist inside the project directory.
    target = (BASE_DIR / filename).resolve()
    if not str(target).startswith(str(BASE_DIR.resolve())) or not target.is_file():
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(BASE_DIR, filename)

@app.get("/api/health")
def health():
    return jsonify({"ok": True, "database": "sqlite", "message": "VeloCart API is running"})

@app.get("/api/analytics/summary")
def analytics_summary():
    """Return a small Pandas-powered summary of the SQLite product catalogue."""
    with get_db() as db:
        products = pd.read_sql_query(
            "SELECT category, price, cost, sold, stock FROM products", db
        )
    if products.empty:
        return jsonify({"product_count": 0, "total_stock": 0, "estimated_sales_value": 0,
                        "categories": []})
    by_category = (products.groupby("category", as_index=False)
                   .agg(product_count=("category", "size"),
                        units_in_stock=("stock", "sum"),
                        units_sold=("sold", "sum")))
    return jsonify({
        "product_count": int(len(products)),
        "total_stock": int(products["stock"].sum()),
        "estimated_sales_value": round(float((products["price"] * products["sold"]).sum()), 2),
        "categories": by_category.to_dict(orient="records"),
    })

@app.get("/api/analytics/revenue-by-category.png")
def revenue_by_category_chart():
    """Create a Matplotlib chart from the sample order CSV using Pandas."""
    csv_path = BASE_DIR / "data" / "sample_orders.csv"
    if not csv_path.exists():
        return jsonify({"error": "Sample orders CSV was not found."}), 404
    orders = pd.read_csv(csv_path)
    if not {"Category", "Revenue"}.issubset(orders.columns):
        return jsonify({"error": "Orders CSV needs Category and Revenue columns."}), 400
    orders["Revenue"] = pd.to_numeric(orders["Revenue"], errors="coerce").fillna(0)
    category_sales = orders.groupby("Category", as_index=False)["Revenue"].sum().sort_values("Revenue", ascending=False)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(category_sales["Category"], category_sales["Revenue"])
    ax.set_title("Sample Revenue by Product Category")
    ax.set_xlabel("Product category")
    ax.set_ylabel("Revenue")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    image_buffer = io.BytesIO()
    fig.savefig(image_buffer, format="png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    image_buffer.seek(0)
    from flask import send_file
    return send_file(image_buffer, mimetype="image/png", download_name="revenue-by-category.png")

@app.get("/api/products")
def list_products():
    with get_db() as db:
        rows = db.execute("SELECT * FROM products ORDER BY rowid").fetchall()
    return jsonify({"products": [row_to_product(row) for row in rows]})

@app.post("/api/products")
def create_product():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    category = str(payload.get("category", "")).strip()
    try:
        price = float(payload.get("price"))
        cost = float(payload.get("cost", 0))
        stock = int(payload.get("stock", 0))
        sold = int(payload.get("sold", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Price, cost, stock and sold must be valid numbers."}), 400
    if not name or not category:
        return jsonify({"error": "Product name and category are required."}), 400
    if price <= 0 or cost < 0 or cost > price or stock < 0 or sold < 0:
        return jsonify({"error": "Check price, cost, stock and sold values."}), 400
    product_id = "custom-" + re.sub(r"[^a-z0-9]", "", os.urandom(8).hex())
    image = str(payload.get("image") or "assets/product-photos/water-bottle.jpg")
    with get_db() as db:
        db.execute("""
            INSERT INTO products (id, name, category, price, cost, sold, stock, image)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (product_id, name, category, price, cost, sold, stock, image))
        row = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    return jsonify({"product": row_to_product(row)}), 201

@app.patch("/api/products/<product_id>")
def update_product(product_id):
    payload = request.get_json(silent=True) or {}
    allowed = {"name", "category", "price", "cost", "sold", "stock", "image"}
    changes = {key: payload[key] for key in allowed if key in payload}
    if not changes:
        return jsonify({"error": "No supported product changes were provided."}), 400
    for field in ("name", "category", "image"):
        if field in changes:
            changes[field] = str(changes[field]).strip()
            if field in ("name", "category") and not changes[field]:
                return jsonify({"error": f"{field.title()} cannot be empty."}), 400
    try:
        for field in ("price", "cost"):
            if field in changes: changes[field] = float(changes[field])
        for field in ("sold", "stock"):
            if field in changes: changes[field] = int(changes[field])
    except (TypeError, ValueError):
        return jsonify({"error": "Numeric fields contain an invalid value."}), 400
    with get_db() as db:
        row = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if row is None:
            return jsonify({"error": "Product not found."}), 404
        merged = row_to_product(row)
        merged.update(changes)
        if merged["price"] <= 0 or merged["cost"] < 0 or merged["cost"] > merged["price"] or merged["stock"] < 0 or merged["sold"] < 0:
            return jsonify({"error": "Check that price is positive, cost is not above price, and stock/sold are not negative."}), 400
        assignments = ", ".join(f"{key} = ?" for key in changes)
        values = list(changes.values()) + [product_id]
        db.execute(f"UPDATE products SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", values)
        updated = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    return jsonify({"product": row_to_product(updated)})

init_db()

if __name__ == "__main__":
    print("VeloCart is running at http://127.0.0.1:5000")
    print(f"Database file: {DB_PATH}")
    # Local development only. For access from other computers, deploy this app to a trusted host.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
