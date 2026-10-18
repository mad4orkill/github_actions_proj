"""Mock backend tools for the POC. Replace these with authenticated service/API calls."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

# Demo-only in-memory data. Production: database + transactional seat locking.
SHOWS = [
    {"show_id": "show_101", "movie": "Galaxy Quest", "theatre": "PVR Orion",
     "date": "2026-10-10", "time": "19:00", "currency": "INR", "seat_price": 250},
    {"show_id": "show_102", "movie": "Galaxy Quest", "theatre": "PVR Orion",
     "date": "2026-10-10", "time": "21:30", "currency": "INR", "seat_price": 220},
]
SEATS = {
    "show_101": ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4"],
    "show_102": ["C1", "C2", "C3", "C4"],
}
BOOKINGS = {}
PAYMENTS = {}
USED_IDEMPOTENCY = {}


def search_shows(movie: str, theatre: str, date: str) -> dict:
    """Search available shows by movie, theatre and ISO date YYYY-MM-DD."""
    results = [
        s for s in SHOWS
        if movie.lower() in s["movie"].lower()
        and theatre.lower() in s["theatre"].lower()
        and date == s["date"]
    ]
    return {"shows": results}


def check_seats(show_id: str) -> dict:
    """Return seats that are currently available for a show."""
    if show_id not in SEATS:
        return {"ok": False, "error": "SHOW_NOT_FOUND"}
    booked = set()
    for b in BOOKINGS.values():
        if b["show_id"] == show_id and b["status"] in ("HELD", "CONFIRMED"):
            if datetime.fromisoformat(b["expires_at"]) > datetime.now(timezone.utc) or b["status"] == "CONFIRMED":
                booked.update(b["seats"])
    return {"show_id": show_id, "available_seats": [s for s in SEATS[show_id] if s not in booked]}


def reserve_seats(show_id: str, seats: list[str], user_id: str, idempotency_key: str) -> dict:
    """Hold seats temporarily. Requires prior user approval in the orchestration workflow."""
    if idempotency_key in USED_IDEMPOTENCY:
        return USED_IDEMPOTENCY[idempotency_key]
    show = next((s for s in SHOWS if s["show_id"] == show_id), None)
    if not show:
        return {"ok": False, "error": "SHOW_NOT_FOUND"}
    if not seats or len(seats) != len(set(seats)):
        return {"ok": False, "error": "INVALID_SEAT_SELECTION"}
    available = check_seats(show_id)["available_seats"]
    if any(seat not in available for seat in seats):
        return {"ok": False, "error": "SEAT_UNAVAILABLE", "available_seats": available}
    booking_id = "bk_" + uuid4().hex[:10]
    expires = datetime.now(timezone.utc) + timedelta(minutes=5)
    booking = {
        "ok": True, "booking_id": booking_id, "user_id": user_id,
        "show_id": show_id, "seats": seats, "amount": show["seat_price"] * len(seats),
        "currency": show["currency"], "status": "HELD",
        "expires_at": expires.isoformat()
    }
    BOOKINGS[booking_id] = booking
    USED_IDEMPOTENCY[idempotency_key] = booking
    return booking


def get_booking(booking_id: str) -> dict:
    """Fetch authoritative booking status and amount."""
    booking = BOOKINGS.get(booking_id)
    if not booking:
        return {"ok": False, "error": "BOOKING_NOT_FOUND"}
    return booking


def create_payment(booking_id: str, amount: int, method: str, idempotency_key: str) -> dict:
    """Create a demo payment request. Production should return a provider-hosted checkout URL."""
    if idempotency_key in USED_IDEMPOTENCY:
        return USED_IDEMPOTENCY[idempotency_key]
    booking = BOOKINGS.get(booking_id)
    if not booking or booking["status"] != "HELD":
        return {"ok": False, "error": "BOOKING_NOT_PAYABLE"}
    if datetime.fromisoformat(booking["expires_at"]) <= datetime.now(timezone.utc):
        return {"ok": False, "error": "HOLD_EXPIRED"}
    if amount != booking["amount"]:
        return {"ok": False, "error": "AMOUNT_MISMATCH"}
    if method.upper() not in ("UPI", "CARD", "NETBANKING"):
        return {"ok": False, "error": "UNSUPPORTED_PAYMENT_METHOD"}
    payment_id = "pay_" + uuid4().hex[:10]
    # Explicit simulation only: do not use this as a real payment implementation.
    payment = {
        "ok": True, "payment_id": payment_id, "booking_id": booking_id,
        "amount": amount, "currency": booking["currency"], "method": method.upper(),
        "status": "PENDING", "demo_checkout_url": "https://example.invalid/demo-checkout"
    }
    PAYMENTS[payment_id] = payment
    USED_IDEMPOTENCY[idempotency_key] = payment
    return payment


def verify_payment(payment_id: str) -> dict:
    """Verify payment status. DEMO ONLY: marks the mock payment successful."""
    payment = PAYMENTS.get(payment_id)
    if not payment:
        return {"ok": False, "status": "UNKNOWN", "error": "PAYMENT_NOT_FOUND"}
    # Simulated provider result for this POC; replace with provider API/webhook verification.
    payment["status"] = "SUCCEEDED"
    booking = BOOKINGS[payment["booking_id"]]
    booking["status"] = "CONFIRMED"
    booking["ticket_id"] = "tkt_" + uuid4().hex[:10]
    return {"ok": True, "payment_id": payment_id, "status": payment["status"],
            "booking_id": booking["booking_id"], "ticket_id": booking["ticket_id"]}


def request_refund(payment_id: str, reason: str, idempotency_key: str) -> dict:
    """Mock a refund request. Production must enforce policy and authorization."""
    if idempotency_key in USED_IDEMPOTENCY:
        return USED_IDEMPOTENCY[idempotency_key]
    payment = PAYMENTS.get(payment_id)
    if not payment or payment["status"] != "SUCCEEDED":
        return {"ok": False, "error": "PAYMENT_NOT_REFUNDABLE"}
    result = {"ok": True, "payment_id": payment_id, "refund_id": "rf_" + uuid4().hex[:10],
              "status": "REFUND_REQUESTED", "reason": reason}
    USED_IDEMPOTENCY[idempotency_key] = result
    return result
