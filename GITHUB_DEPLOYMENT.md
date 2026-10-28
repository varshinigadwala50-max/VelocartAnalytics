# Publish VeloCart

1. Create a public GitHub repository named `velocart-dashboard`.
2. Open this folder in VS Code and run:

```bash
git init
git add .
git commit -m "Build VeloCart analytics dashboard"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/velocart-dashboard.git
git push -u origin main
```

3. On GitHub, go to Settings → Pages → Deploy from a branch → `main` → `/(root)` → Save.
4. GitHub Pages will publish a URL like `https://YOUR-USERNAME.github.io/velocart-dashboard/landing.html`.

This is a static front-end demo. Static hosting will not run the Python Streamlit/backend files; deploy those separately on a Python-capable host if you need the backend online. Do not use the demo login for real credentials.
