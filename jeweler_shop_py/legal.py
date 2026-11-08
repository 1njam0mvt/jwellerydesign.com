"""Privacy Policy and Terms text. Have a lawyer review for your jurisdiction (written for India)."""
from config import PREBOOK, SITE

UPDATED = "28 October 2026"
PRIVACY = [
    ("1. Who we are", f'{SITE["legal_name"]} ("we") operates this website and our store at {SITE["address"]}.'),
    ("2. Data we collect", "Contact details; order, pre-booking and deposit records; old gold/silver details you submit (weight, purity, photos); identity and address proof where law requires; reviews you upload; technical data (IP, device, cookies)."),
    ("3. Why we use it", "To fulfil orders, pre-bookings and exchanges; to meet tax, hallmarking and anti-money-laundering duties; to prevent fraud; and to send offers only with your consent, which you can withdraw anytime."),
    ("4. Secure payments", "Payments, including pre-booking deposits, are handled by a PCI-DSS compliant gateway (Stripe) over encrypted connections. We never see or store your card number, CVV or UPI PIN."),
    ("5. Sharing", "Payment gateways, insured couriers, assay laboratories, hosting and analytics providers, advisers and regulators when legally required. We do not sell personal data."),
    ("6. Retention and security", "We keep records as long as tax and accounting law requires. We use TLS encryption, access controls and regular reviews, and will notify you and authorities of a breach as the law requires."),
    ("7. Your rights", f'You may request access, correction or erasure, withdraw consent, and raise a grievance under applicable law (including India\'s DPDP Act, 2023). Write to {SITE["email"]}.'),
    ("8. Children and changes", "Our services are for adults. Updates are posted on this page with a new date."),
]
TERMS = [
    ("1. Acceptance", f'By using this site or buying from {SITE["name"]} you agree to these terms.'),
    ("2. Prices and metal-rate fluctuations", "Gold and silver rates change several times a day. Prices and calculators here are estimates at the rate shown. The final price is the rate at billing (or the locked rate under clause 5) plus making charges and taxes. Sample rates, if shown, are illustrative only."),
    ("3. Making charges and taxes", "Making (labour) charges are quoted as a percentage of metal value or per gram, vary by design, and are shown separately. GST is charged as per law. Making charges are not credited back on exchange or buy-back unless your invoice says so."),
    ("4. Purity and hallmarking", "Gold jewellery is sold BIS-hallmarked as required by law. Purity and weights are stated on the invoice; small variations are possible in handcrafted pieces."),
    ("5. Pre-booking and deposits", f'A deposit ({", ".join(str(p) + "%" for p in PREBOOK["deposit_options"])} options) locks the metal rate for {PREBOOK["lock_hours"]} hours from payment confirmation. The balance is due within {PREBOOK["balance_days"]} days, after which the billing-day rate applies. You may cancel for a refund (less gateway charges) before production or stone procurement starts. Once a bespoke design is approved, the deposit covers costs incurred and is non-refundable, except where we fail to deliver, in which case it is refunded in full.'),
    ("6. Customisation", "Engraved, resized or custom-made items cannot be returned unless defective. Please check the proof before approving."),
    ("7. Old gold and silver exchange", "Online values are indicative. The final value is set after purity testing and weighing in your presence, after deducting melting or testing loss. ID and ownership proof may be required. You may decline the offer."),
    ("8. Delivery and pickup", "Deliveries and pickups are insured and need ID verification and signature. Report damage within 24 hours of receipt."),
    ("9. Returns", "Ready-made, unworn items with invoice, hallmark and packaging may be exchanged within 7 days of delivery. Custom, engraved and limited-edition items are excluded."),
    ("10. Previews", "3D previews and photos are illustrative; colour and size may differ slightly on the physical piece."),
    ("11. Liability and law", f'To the extent permitted by law our liability is limited to the amount paid for the item concerned. These terms are governed by the laws of India; courts at {SITE["city"]} have jurisdiction, subject to any consumer forum you may lawfully approach.'),
]
