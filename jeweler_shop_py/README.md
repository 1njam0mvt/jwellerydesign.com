# Luxury 3D Jeweller Shop (Python + HTML)

Flask backend + Jinja HTML templates + vanilla JS + Three.js (loaded from a pinned CDN version).

## Features
- Cinematic 3D intro and ring viewer (orbit/zoom/touch, 24K Yellow Gold / 18K Rose Gold / Platinum material switching)
- Live gold and silver rates (GoldAPI.io, 60 s server cache, stale fallback) with a per-gram price calculator (weight, purity, making charge, GST) and old-gold exchange estimator
- Bento grid landing page (glass, neomorphic, clay, brutalist tiles, tilt-depth effect)
- Pre-booking modal with Stripe Checkout deposit (server computes amount and locked rate)
- `mailto:` and `tel:` quick actions, Privacy Policy, Terms, Contact pages
- SEO: meta + Open Graph, JSON-LD (JewelryStore/LocalBusiness, FAQ, Product helper), sitemap.xml, robots.txt, local SEO playbook in `seo.py`

## Run locally
```
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then edit it (brand details, API keys)
python app.py                   # http://localhost:5000
```
Production: `gunicorn -w 2 -b 0.0.0.0:8000 app:app` behind HTTPS, with `SITE_URL` set to your real domain.

## Files
- `app.py` routes, rates API, Stripe pre-booking, pages, sitemap | `config.py` brand/NAP/business settings | `seo.py` SEO + JSON-LD | `legal.py` legal text
- `templates/` base, index, page | `static/css/style.css` | `static/js/app.js` (rates, calculator, pre-book) | `static/js/viewer.js` (Three.js)

## Before going live
1. Put real brand, address and phone in `.env` (wrong NAP hurts local ranking). Add `static/img/og-default.jpg` and `logo.png`.
2. GoldAPI returns international spot converted to INR, which excludes Indian duty and local premium. Add a markup or use an Indian rate source.
3. Add a Stripe webhook for `checkout.session.completed` to record paid bookings (not included).
4. Have a lawyer review `legal.py`. The rate limiter and rate cache are per process; use Redis if you run many workers.
