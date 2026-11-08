"""All brand, contact (NAP) and business settings. Override any value in the .env file."""
import os
import pathlib


def _load_env() -> None:
    path = pathlib.Path(__file__).with_name(".env")
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env()
e = lambda key, default: os.environ.get(key, default)  # noqa: E731

SITE = {
    "name": e("BRAND_NAME", "Aurelia Fine Jewellers"),
    "legal_name": e("LEGAL_NAME", "Aurelia Fine Jewellers Pvt. Ltd."),
    "tagline": "Hallmarked gold, certified diamonds and bespoke jewellery",
    "url": e("SITE_URL", "http://localhost:5000").rstrip("/"),
    "phone": e("PHONE_DISPLAY", "+91 00000 00000"),
    "phone_e164": e("PHONE_E164", "+910000000000"),
    "email": e("EMAIL", "care@example.com"),
    "street": e("STREET", "1 Jewellers Row"),
    "city": e("CITY", "Kolkata"),
    "region": e("REGION", "West Bengal"),
    "pin": e("PIN", "700001"),
    "lat": float(e("LAT", "22.5726")),
    "lng": float(e("LNG", "88.3639")),
    "maps_url": e("MAPS_URL", "https://maps.google.com/"),
    "hours": [{"label": "Mon-Sat", "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], "opens": "10:30", "closes": "20:00"}],
    "grievance_officer": e("GRIEVANCE_OFFICER", "Grievance Officer"),
    "social": [s for s in e("SOCIAL", "").split(",") if s],
    "price_range": "₹₹₹",
    "gst_percent": 3,
}
SITE["address"] = f'{SITE["street"]}, {SITE["city"]}, {SITE["region"]} {SITE["pin"]}, India'
PREBOOK = {"lock_hours": 72, "balance_days": 30, "deposit_options": [10, 25, 50], "min_value": 5000, "max_value": 10_000_000}
