"""SEO helpers: meta tags, Open Graph, JSON-LD (JewelryStore/LocalBusiness, Product + Offer, FAQ) and the local SEO playbook."""
import datetime
import os
from urllib.parse import urljoin

from config import SITE

CITY = SITE["city"]
KEYWORDS = [
    "best jeweler shop near me", "jewellery shop near me", f"best jewellers in {CITY}", f"gold jewellery shop in {CITY}",
    f"diamond jewellery {CITY}", f"22K gold price today {CITY}", f"sell old gold {CITY}", f"old gold exchange {CITY}",
    f"bridal jewellery {CITY}", f"BIS hallmarked gold jewellery {CITY}", f"silver jewellery {CITY}", f"custom jewellery {CITY}",
]
_OG = os.path.join(os.path.dirname(__file__), "static", "img", "og-default.jpg")


def absolute(path: str = "/") -> str:
    return urljoin(SITE["url"] + "/", path.lstrip("/"))


def build_meta(title=None, description=None, path="/", noindex=False) -> dict:
    return {
        "title": title or f'{SITE["name"]} | Best Jewellers in {CITY}: Gold, Diamond & Silver',
        "description": description or (
            f'{SITE["name"]}, trusted jewellery shop in {CITY}, {SITE["region"]}. BIS hallmarked gold, certified diamonds, '
            "live gold rates, old gold exchange and bespoke pre-booking."),
        "canonical": absolute(path),
        "keywords": ", ".join(KEYWORDS),
        "robots": "noindex,nofollow" if noindex else "index,follow,max-image-preview:large",
        "image": absolute("/static/img/og-default.jpg") if os.path.exists(_OG) else None,
        "geo_position": f'{SITE["lat"]};{SITE["lng"]}',
    }


def store_jsonld(reviews=None) -> dict:
    """Pass reviews={'rating': 4.8, 'count': 120} only with real, on-page reviews."""
    data = {
        "@context": "https://schema.org", "@type": ["JewelryStore", "LocalBusiness"], "@id": absolute("/#store"),
        "name": SITE["name"], "legalName": SITE["legal_name"], "description": SITE["tagline"], "url": SITE["url"],
        "logo": absolute("/static/img/logo.png"), "telephone": SITE["phone_e164"], "email": SITE["email"],
        "priceRange": SITE["price_range"], "currenciesAccepted": "INR",
        "paymentAccepted": "Cash, Credit Card, Debit Card, UPI, Bank Transfer",
        "address": {"@type": "PostalAddress", "streetAddress": SITE["street"], "addressLocality": CITY,
                    "addressRegion": SITE["region"], "postalCode": SITE["pin"], "addressCountry": "IN"},
        "geo": {"@type": "GeoCoordinates", "latitude": SITE["lat"], "longitude": SITE["lng"]},
        "hasMap": SITE["maps_url"], "areaServed": {"@type": "City", "name": CITY},
        "openingHoursSpecification": [{"@type": "OpeningHoursSpecification", "dayOfWeek": h["days"], "opens": h["opens"], "closes": h["closes"]} for h in SITE["hours"]],
        "sameAs": SITE["social"],
    }
    if reviews and reviews.get("count", 0) > 0:
        data["aggregateRating"] = {"@type": "AggregateRating", "ratingValue": reviews["rating"], "reviewCount": reviews["count"]}
    return data


def product_jsonld(p: dict) -> dict:
    """p: slug, name, description, images[], sku, metal, purity, weight_grams, price, in_stock."""
    valid = p.get("price_valid_until") or (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    return {
        "@context": "https://schema.org", "@type": "Product", "name": p["name"], "description": p["description"], "sku": p["sku"],
        "image": [absolute(i) for i in p["images"]], "brand": {"@type": "Brand", "name": SITE["name"]},
        "material": f'{p["purity"]} {p["metal"]}',
        "weight": {"@type": "QuantitativeValue", "value": p["weight_grams"], "unitCode": "GRM"},
        "offers": {"@type": "Offer", "url": absolute(f'/product/{p["slug"]}'), "priceCurrency": "INR", "price": f'{p["price"]:.2f}',
                   "priceValidUntil": valid, "itemCondition": "https://schema.org/NewCondition", "seller": {"@id": absolute("/#store")},
                   "availability": "https://schema.org/InStock" if p.get("in_stock", True) else "https://schema.org/PreOrder"},
    }


def faq_jsonld(qa) -> dict:
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa]}


FAQ = [
    ("How is the jewellery price calculated?", "Price = weight x live metal rate x purity + making charges + 3% GST. Our calculator shows each part."),
    ("Can I exchange my old gold?", "Yes. Estimate the value online, then confirm after purity testing in store or at doorstep pickup."),
    ("How does pre-booking work?", "Pay a deposit to lock today's metal rate for 72 hours and reserve your piece or bespoke design."),
]

LOCAL_SEO_PLAYBOOK = {
    "google_business_profile": ["Claim and verify; primary category 'Jewelry store', plus 'Gold dealer', 'Jewelry buyer'.",
                                "Keep name/address/phone identical to config.py everywhere.", "Add hours, services, 10+ real photos; post weekly."],
    "reviews": ["Share the Google review link by QR at billing and via WhatsApp/SMS.", "Reply to every review within 48h.",
                "Only pass real review totals to store_jsonld()."],
    "on_page": ["One H1 with service + city per page; create /jewellers/<area> pages with unique copy, map and FAQs.",
                "Publish a daily '22K gold price today' page; embed Google Map on /contact."],
    "citations": ["Bing Places, Apple Business Connect, JustDial, Sulekha, IndiaMART, local trade associations."],
    "technical": ["Submit /sitemap.xml in Search Console.", "LCP < 2.5s, INP < 200ms, CLS < 0.1.", "Mobile-first; HTTPS; alt text on all images."],
}
