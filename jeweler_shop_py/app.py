"""Luxury jeweller shop: Flask backend (live rates, Stripe pre-booking, SEO, legal pages). Run: python app.py"""
import hashlib
import json
import logging
import os
import re
import threading
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

from flask import Flask, Response, abort, jsonify, render_template, request

import config
import legal
import seo
from config import PREBOOK, SITE

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10_000
log = logging.getLogger("jeweller")
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------- live rates
TROY_OUNCE_G, TTL, STALE_MAX = 31.1034768, 60, 900
_cache = {"snap": None, "at": 0.0}
_lock = threading.Lock()  # also de-duplicates concurrent upstream calls


class RatesUnavailable(Exception):
    pass


def _pos(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0 else None


def _fetch(symbol: str, key: str) -> dict:
    req = urllib.request.Request(f"https://www.goldapi.io/api/{symbol}/INR", headers={"x-access-token": key, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.load(resp)
    except (urllib.error.URLError, ValueError, TimeoutError) as exc:
        raise RatesUnavailable(f"{symbol}: {exc}") from exc
    if not isinstance(data, dict) or data.get("error"):
        raise RatesUnavailable(f"{symbol}: provider error")
    return data


def _refresh() -> dict:
    key = os.environ.get("METALS_API_KEY")
    if not key:
        raise RatesUnavailable("METALS_API_KEY is not configured")
    gold, silver = _fetch("XAU", key), _fetch("XAG", key)
    g24 = _pos(gold.get("price_gram_24k")) or (_pos(gold.get("price")) and gold["price"] / TROY_OUNCE_G)
    sil = (_pos(silver.get("price")) and silver["price"] / TROY_OUNCE_G) or _pos(silver.get("price_gram_24k"))
    if not g24 or not sil or sil >= g24:
        raise RatesUnavailable("provider returned invalid rates")
    r2 = lambda n: round(n, 2)  # noqa: E731
    snap = {"rates": {"gold24": r2(g24), "gold22": r2(_pos(gold.get("price_gram_22k")) or g24 * 22 / 24),
                      "gold18": r2(_pos(gold.get("price_gram_18k")) or g24 * 18 / 24), "silver": r2(sil)},
            "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())}
    _cache.update(snap=snap, at=time.time())
    return snap


def get_rates() -> dict:
    with _lock:
        age = time.time() - _cache["at"]
        if _cache["snap"] and age < TTL:
            return {**_cache["snap"], "stale": False}
        try:
            return {**_refresh(), "stale": False}
        except RatesUnavailable:
            if _cache["snap"] and age < STALE_MAX:
                return {**_cache["snap"], "stale": True}
            raise


@app.get("/api/rates")
def api_rates():
    try:
        d = get_rates()
    except RatesUnavailable as exc:
        log.error("rates unavailable: %s", exc)
        return jsonify(success=False, error="Live rates are temporarily unavailable"), 503, {"Cache-Control": "no-store", "Retry-After": "30"}
    body = {"success": True, "rates": d["rates"], "currency": "INR", "unit": "per_gram", "updatedAt": d["updatedAt"]}
    if d["stale"]:
        body["stale"] = True
    return jsonify(body), 200, {"Cache-Control": "public, s-maxage=60, stale-while-revalidate=120"}


# ---------------------------------------------------------------- pre-booking (Stripe Checkout)
METAL_LABEL = {"24": "Gold 24K", "22": "Gold 22K", "18": "Gold 18K", "S925": "Silver 925"}
_hits: dict = {}


def _limited(ip: str) -> bool:
    now = time.time()
    if len(_hits) > 5000:
        for k in [k for k, v in _hits.items() if v[1] < now]:
            del _hits[k]
    n, reset = _hits.get(ip, (0, 0))
    if reset < now:
        _hits[ip] = (1, now + 60)
        return False
    _hits[ip] = (n + 1, reset)
    return n + 1 > 5


def _clean(v, n):
    return re.sub(r"[\x00-\x1f\x7f]", " ", v).strip()[:n] if isinstance(v, str) else ""


def _err(msg, code, headers=None):
    return jsonify(success=False, error=msg), code, headers or {}


@app.post("/api/prebook")
def api_prebook():
    if not os.environ.get("STRIPE_SECRET_KEY"):
        log.error("STRIPE_SECRET_KEY is not configured")
        return _err("Online payments are not available right now", 503)
    origin = request.headers.get("Origin")
    allowed = {f'{urlparse(SITE["url"]).scheme}://{urlparse(SITE["url"]).netloc}', request.host_url.rstrip("/")}
    if origin and origin not in allowed:
        return _err("Forbidden", 403)
    ip = (request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")).split(",")[0].strip()
    if _limited(ip):
        return _err("Too many attempts. Please wait a minute and try again.", 429, {"Retry-After": "60"})

    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _err("Invalid JSON", 400)
    name, phone = _clean(body.get("name"), 100), _clean(body.get("phone"), 20)
    email, item, metal = _clean(body.get("email"), 120).lower(), _clean(body.get("item"), 150), _clean(body.get("metal"), 4)
    try:
        value, pct = float(body.get("estimatedValue")), int(body.get("depositPercent"))
    except (TypeError, ValueError):
        return _err("Invalid amount", 400)

    if len(name) < 2: return _err("Enter your full name", 400)  # noqa: E701
    if not re.fullmatch(r"[+()\d\s-]{8,16}", phone): return _err("Enter a valid phone number", 400)  # noqa: E701
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email): return _err("Enter a valid email", 400)  # noqa: E701
    if len(item) < 3: return _err("Describe the item", 400)  # noqa: E701
    if metal not in METAL_LABEL: return _err("Invalid metal", 400)  # noqa: E701
    if not (PREBOOK["min_value"] <= value <= PREBOOK["max_value"]):
        return _err(f'Estimated value must be between ₹{PREBOOK["min_value"]:,} and ₹{PREBOOK["max_value"]:,}', 400)
    if pct not in PREBOOK["deposit_options"]: return _err("Invalid deposit option", 400)  # noqa: E701

    # Deposit and locked rate are computed server-side; client-sent figures are ignored.
    try:
        r = get_rates()["rates"]
    except RatesUnavailable as exc:
        log.error("prebook: rates unavailable: %s", exc)
        return _err("We cannot lock a rate right now. Please try again shortly.", 503)
    locked = round({"24": r["gold24"], "22": r["gold22"], "18": r["gold18"]}.get(metal, r["silver"] * 925 / 999), 2)
    deposit = round(value * pct / 100)
    meta = {"customer_name": name, "customer_phone": phone, "item": item, "metal": METAL_LABEL[metal],
            "estimated_value_inr": str(round(value)), "deposit_percent": str(pct), "deposit_inr": str(deposit),
            "locked_rate_per_gram_inr": str(locked), "lock_hours": str(PREBOOK["lock_hours"]), "balance_due_days": str(PREBOOK["balance_days"])}
    idem = hashlib.sha256("|".join(map(str, [email, item, metal, value, pct, locked, int(time.time() // 300)])).encode()).hexdigest()
    base = SITE["url"]
    try:
        import stripe
        stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
        session = stripe.checkout.Session.create(
            mode="payment", customer_email=email,
            line_items=[{"quantity": 1, "price_data": {"currency": "inr", "unit_amount": deposit * 100, "product_data": {
                "name": f'Pre-booking deposit ({pct}%) · {SITE["name"]}',
                "description": f'{item}. {METAL_LABEL[metal]} rate locked at ₹{locked}/g for {PREBOOK["lock_hours"]} hours.'[:300]}}}],
            metadata=meta, payment_intent_data={"description": f"Pre-booking deposit: {item}"[:300], "metadata": meta},
            expires_at=int(time.time()) + 1800,
            success_url=f"{base}/?prebook=success&session_id={{CHECKOUT_SESSION_ID}}", cancel_url=f"{base}/?prebook=cancelled",
            idempotency_key=idem)
        if not session.url:
            raise RuntimeError("Stripe returned no checkout URL")
        return jsonify(success=True, checkoutUrl=session.url), 200, {"Cache-Control": "no-store"}
    except Exception as exc:  # stripe.StripeError and anything unexpected
        log.error("prebook failed: %s", exc)
        return _err("We could not start checkout. Please try again or contact us.", 502)


# ---------------------------------------------------------------- pages and SEO
@app.context_processor
def inject():
    client = {"name": SITE["name"], "phone_e164": SITE["phone_e164"], "email": SITE["email"], "gst": SITE["gst_percent"],
              "lock_hours": PREBOOK["lock_hours"], "balance_days": PREBOOK["balance_days"], "deposit_options": PREBOOK["deposit_options"]}
    return {"site": SITE, "prebook": PREBOOK, "client": client}


@app.get("/")
def index():
    return render_template("index.html", meta=seo.build_meta(path="/"), ld=[seo.store_jsonld(), seo.faq_jsonld(seo.FAQ)], faq=seo.FAQ)


@app.get("/privacy")
def privacy():
    return render_template("page.html", kind="legal", heading="Privacy Policy", sections=legal.PRIVACY, updated=legal.UPDATED,
                           meta=seo.build_meta(f'Privacy Policy | {SITE["name"]}', "How we collect, use and protect your data.", "/privacy"), ld=[])


@app.get("/terms")
def terms():
    return render_template("page.html", kind="legal", heading="Terms & Conditions", sections=legal.TERMS, updated=legal.UPDATED,
                           meta=seo.build_meta(f'Terms & Conditions | {SITE["name"]}', "Pricing, making charges, pre-booking and exchange terms.", "/terms"), ld=[])


@app.get("/contact")
def contact():
    return render_template("page.html", kind="contact", heading="Contact & Customer Support",
                           meta=seo.build_meta(f'Contact Us | {SITE["name"]}, {SITE["city"]}', f'Visit, call or email {SITE["name"]} in {SITE["city"]}.', "/contact"), ld=[seo.store_jsonld()])


@app.get("/robots.txt")
def robots():
    return Response(f"User-agent: *\nAllow: /\nDisallow: /api/\nSitemap: {seo.absolute('/sitemap.xml')}\n", mimetype="text/plain")


@app.get("/sitemap.xml")
def sitemap():
    urls = "".join(f"<url><loc>{seo.absolute(p)}</loc></url>" for p in ("/", "/contact", "/privacy", "/terms"))
    return Response(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>', mimetype="application/xml")


@app.errorhandler(404)
def not_found(_):
    return render_template("page.html", kind="legal", heading="Page not found", sections=[("", "The page you are looking for does not exist.")], updated=None,
                           meta=seo.build_meta("Page not found", noindex=True), ld=[]), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=os.environ.get("FLASK_DEBUG") == "1")
