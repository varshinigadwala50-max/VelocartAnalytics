# VeloCart — E-commerce Business Intelligence Demo

A responsive, interactive e-commerce analytics frontend inspired by the navy/white/teal reference screenshots. It includes a branded sign-in page with a dashboard preview, large photographic-style product imagery, functional sidebar pages, weekly/monthly/yearly report selection, inventory review actions, a discount calculator, settings, cursor motion, and CSV export.

## Run on Windows
1. Download and extract the ZIP fully.
2. Open the extracted `velocart` folder.
3. Double-click `RUN_VELOCART.bat` (requires Python 3 only to serve the static files locally).
4. Your browser opens `http://127.0.0.1:8000/landing.html`. Keep the terminal window open while using the site.
5. Use the prefilled demo email/password, or enter any valid email and non-empty password.

Alternative: open `landing.html` in Chrome or Edge. Do not open `app.js` or `styles.css` directly; those are source code files.

## Included files
- `landing.html` — login screen, VeloCart logo and analytics preview background.
- `index.html` — dashboard shell and overview.
- `styles.css` — theme, responsive layouts, hover and cursor effects.
- `app.js` — product data, working navigation views, reporting-period selector, inventory actions, discount calculator, settings and CSV export.
- `assets/brand/` — VeloCart SVG logo files.
- `assets/product-photos/` — 16 locally stored, photorealistic demo product images (electronics, beauty, appliances and home/lifestyle items).
- `assets/products/` — legacy SVG illustrations retained for compatibility.
- `admin_app.py`, `customer_app.py`, `metrics.py`, `data_loader.py`, `schema.sql`, and `data/` — starter Python/database components for future integration.

## Working dashboard sections
- **Overview:** KPI cards, revenue chart, category share, featured products and inventory preview.
- **Sales analytics:** period-aware metrics, revenue chart, category breakdown and best-selling products.
- **Inventory health:** stock status filter and simulated restock action.
- **All products:** photo catalog, text search and category filter; the Add Product button adds a local demo item.
- **Business insights:** practical sample-data observations and quick links.
- **Reports:** weekly/monthly/yearly selector and CSV download.
- **Discount planner:** choose a product and discount percentage to calculate discounted price and estimated gross margin.
- **Settings:** change the displayed name and reset the demo.

## Important limitations
This is an educational frontend demo using illustrative sample data. The product photos are photographic-style demo assets, not verified photographs of actual products or endorsement by the brands that may appear in generated imagery. Login is browser-based demo authentication, not secure production authentication. Weekly/monthly/yearly revenue and orders are illustrative snapshots rather than calculations from dated transactions. Inventory edits and added products are held in browser memory and reset when the page reloads. The included Python files are not automatically run by the static launcher.

## GitHub Pages
Push the contents of this folder to the repository root and enable **Settings → Pages → Deploy from a branch → `main` → `/(root)`**. Open the published `landing.html` path to start at the login page. For a cleaner root URL, rename the dashboard `index.html` to `dashboard.html`, rename `landing.html` to `index.html`, and update the login redirect in `landing.html` to `dashboard.html` before publishing.


## Shared product database (new)

The original dashboard design is preserved. The dashboard now reads product data from a Flask API backed by SQLite. Add-product, edit-price, and restock changes are saved in `velocart.db`; browser tabs connected to the same running server refresh automatically about every 4 seconds.

### Run on Windows

1. Install Python 3 if it is not installed.
2. Extract the ZIP and open the `velocart-final-verified` folder in VS Code.
3. Double-click `RUN_VELOCART.bat`, or open a VS Code terminal in this folder and run:
   `py -m pip install -r requirements.txt`
   `py server.py`
4. Open `http://127.0.0.1:5000` in your browser.
5. Sign in through the demo landing page. Use the prefilled demo credentials or any valid email and non-empty password.

Do not open `index.html` by double-clicking it: the page must be served by `server.py` so `/api/products` can reach the database.

### Testing shared updates

Open `http://127.0.0.1:5000` in two browser windows on the same computer. Add a product, edit a product price from a table view, or restock an item in one window. The other window should update within about 4 seconds.

### To sync between different computers

The app must be deployed to an online Python host and use one shared persistent database. Running `server.py` only on your laptop syncs browsers that connect to that same laptop/server; it does not automatically sync a friend who is using a separate copy or a separate GitHub Pages URL. For an online deployment, use a trusted host that supports Flask and persistent storage, set `PORT` if the host provides one, and set `VELOCART_DB_PATH` to a persistent disk path. Do not use an ephemeral filesystem for the SQLite database. GitHub Pages cannot run this Python backend.

### Important demo security note

The sign-in page is still demo-only: it accepts any valid email and non-empty password and is not secure authentication. Do not publish this app with real customer information or sensitive business data until proper authentication, authorization, HTTPS, and production database security are implemented.


## Optional online deployment setup

A `Procfile` is included for hosts that run Python web services: `gunicorn server:app`.
For a multi-computer shared deployment:
- Push this folder to a GitHub repository (the repository root should contain `server.py`, `requirements.txt`, `Procfile`, `index.html`, `landing.html`, `app.js`, `styles.css`, and `assets/`).
- Create a Python web service from that repository on a host that supports Flask.
- Attach a persistent disk/volume and set `VELOCART_DB_PATH` to a file on that volume (for example `/data/velocart.db` if the host mounts the volume at `/data`).
- Use the host's public HTTPS URL for both you and your friend. Both must use that same URL; do not use the old GitHub Pages URL for the dashboard.
- Keep demo-only login in mind: this project is not production-secure and should not be used with real personal or business data.

The app can be tested locally first with `py server.py`. Hosting is a separate deployment step; the ZIP itself does not automatically publish the app to the internet.


## Python analytics stack (for the project review)

- **Pandas** (`data_loader.py`, `metrics.py`, and `/api/analytics/summary`) cleans order CSV data, groups products by category, and calculates summary metrics.
- **Matplotlib** (`/api/analytics/revenue-by-category.png`) generates a PNG chart from `data/sample_orders.csv`. Start the Flask server and open `http://127.0.0.1:5000/api/analytics/revenue-by-category.png` to view it.
- **SQLite** (`server.py`) stores the product catalogue and persists product edits. SQLite is built into Python, so a separate database server is not needed.

The current front-end charts are still rendered by the existing JavaScript. These Python endpoints demonstrate the required Python analytics stack separately; GitHub Pages cannot run these endpoints. Run/deploy the Flask app to use them. The analytics CSV and dashboard figures are sample/demo data, not live store transactions.
