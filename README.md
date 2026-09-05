# Puku Kosheli Hub — Nepali Achar E-commerce

Premium traditional Nepali achar (pickle) brand website for **Puku Kosheli Hub**, Urlabari, Morang, Nepal.

**Stack:** Flask · PostgreSQL (Neon) · Cloudinary · Vanilla JS · HTML/CSS · Vercel-compatible

## Features

- 100% Nepali customer-facing UI
- Product catalog with categories, search, filters
- Shopping cart (session-based, server-validated prices)
- Checkout: delivery / pickup, COD / bank / QR
- Order tracking with visual timeline
- Admin panel: products, categories, orders, stock, reviews, gallery, settings
- Cloudinary image uploads
- SEO: meta, OG, sitemap, robots, structured data
- Mobile-first premium design

## Requirements

- Python 3.11+
- Neon PostgreSQL (or any PostgreSQL)
- Cloudinary account (for images)
- (Optional) Vercel for deployment

## Local Setup

```bash
# Clone / extract project
cd puku-kosheli-hub

# Virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Dependencies
pip install -r requirements.txt

# Environment
cp .env.example .env
# Edit .env with your SECRET_KEY, DATABASE_URL, Cloudinary keys
```

### Neon PostgreSQL

1. Create a project at [neon.tech](https://neon.tech)
2. Copy the connection string into `DATABASE_URL` in `.env`
3. Ensure it uses `postgresql://` (not `postgres://`)

### Cloudinary

1. Sign up at [cloudinary.com](https://cloudinary.com)
2. Set `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`

### Database migrations

```bash
export FLASK_APP=run.py
flask db init          # first time only
flask db migrate -m "Initial"
flask db upgrade
```

For local quick start without Neon, SQLite is used if `DATABASE_URL` is unset (`sqlite:///dev.db`). Production must use PostgreSQL.

### Seed settings & create admin

```bash
flask seed-settings
flask create-admin
# Or set ADMIN_EMAIL and ADMIN_PASSWORD in env before create-admin
```

### Run

```bash
python run.py
# → http://127.0.0.1:5000
```

Admin: `http://127.0.0.1:5000/auth/login`

## Vercel Deployment

1. Push code to GitHub
2. Import project in Vercel
3. Set environment variables:
   - `SECRET_KEY`
   - `DATABASE_URL` (Neon)
   - `CLOUDINARY_CLOUD_NAME`
   - `CLOUDINARY_API_KEY`
   - `CLOUDINARY_API_SECRET`
   - `FLASK_ENV=production`
4. Deploy

`vercel.json` routes all requests to `run.py`.

After deploy, run migrations once (e.g. via a one-off job or local against production DB):

```bash
DATABASE_URL=your-neon-url flask db upgrade
flask seed-settings
flask create-admin
```

## Project structure

```
app/
  auth/          Login/logout
  main/          Home, about, gallery, contact, track
  products/      Catalog & detail
  cart/          Cart API & page
  orders/        Checkout & success
  admin/         Full admin dashboard
  templates/     Jinja2 templates (Nepali UI)
  static/        CSS, JS
  models.py      SQLAlchemy models
  extensions.py  db, migrate, login, csrf
  utils.py       Cloudinary, slugify, helpers
config.py
run.py
vercel.json
```

## Admin workflow

1. Login → Dashboard
2. Categories → add आँपको अचार, खुर्सानीको अचार, etc.
3. Products → add with images (Cloudinary), price, stock
4. Settings → phone, WhatsApp, delivery charges, payment info, TikTok
5. Orders → update status as you prepare/deliver
6. Reviews → approve customer feedback
7. Gallery → upload brand photos

## Security notes

- Passwords hashed with Werkzeug
- CSRF on forms
- Session cookies HttpOnly / SameSite
- Secrets only via environment variables
- Prices always re-read from DB at checkout
- Stock decremented on confirmed order

## Troubleshooting

| Issue | Fix |
|-------|-----|
| DB connection | Check `DATABASE_URL`, SSL, Neon idle timeout |
| Images fail | Verify Cloudinary env vars |
| CSRF errors | Ensure `SECRET_KEY` is set and stable |
| 403 on admin | Login as admin role user |
| Empty products | Add via Admin → Products |

## License

Built for Puku Kosheli Hub, Urlabari, Morang, Nepal.
© All rights reserved for the brand owner.
