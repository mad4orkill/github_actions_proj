# Agentic Movie Ticket Booking POC (Google ADK)

This is an interview/demo scaffold with **two domain agents** (Booking Agent and Payment Agent) plus a Root Orchestrator. It uses mocked movie and payment services so it does not make real bookings or charge money.

## Architecture
User/UI -> API layer (production) -> Root Orchestrator -> Booking Agent -> Payment Agent -> confirmation.
- Booking Agent: search shows, check seats, reserve seats, read booking.
- Payment Agent: create payment intent, verify payment, request refund.
- Root Orchestrator: gathers missing details, delegates in sequence, checks final state.
- Business rules and transaction state belong in backend services/database, not in the LLM.

## Project structure
```text
movie_ticket_agentic_poc/
├── main.py
├── tools.py
├── requirements.txt
├── .env.example
└── skills/
    ├── booking/SKILL.md
    └── payment/SKILL.md
```

## Run
Python 3.10+ recommended.
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
adk web
```
Run `adk web` from the directory containing `main.py` only after adapting it to the standard ADK project layout if your installed ADK version expects an agent package. For a quick local smoke test, use the Python ADK runner documented for your installed version.

This is a POC scaffold; ADK APIs can change between versions. The tools below are synchronous Python functions and are intentionally easy to replace with REST calls.

## Important production controls
1. Use a database transaction and unique seat-lock constraints to prevent double booking.
2. Give every booking/payment operation an idempotency key.
3. Seat reservations must expire automatically (e.g. after 5 minutes).
4. Verify payment server-to-server or via a signed webhook; never trust user-provided screenshots or an LLM claim.
5. Do not store card numbers, CVVs, UPI PINs, or payment secrets in prompts/logs.
6. Confirm only when the booking service sees a valid reservation AND the payment provider confirms capture.
7. If payment fails, release the seat hold. If payment succeeds but confirmation fails, reconcile and either complete booking or refund; don't blindly retry a charge.
8. Require explicit user approval before charging, booking non-refundable tickets, or refunding.
9. Add authentication, authorization, rate limiting, audit logs, metrics, tracing, and secrets management.

## Example conversation
User: "Book 2 tickets for Galaxy Quest at PVR Orion, 7 PM, today."
Agent: asks which date if "today" cannot be reliably resolved, then offers available shows/seats and authoritative price.
Agent: asks user to confirm the chosen show/seats and total.
Booking Agent: reserves seats and returns booking ID + expiry.
Payment Agent: creates a payment request and verifies provider status.
Orchestrator: confirms only if both booking and payment states are verified.

## Tool contracts
- `search_shows(movie, theatre, date) -> list[show]`
- `check_seats(show_id) -> list[seat]`
- `reserve_seats(show_id, seats, user_id, idempotency_key) -> booking`
- `get_booking(booking_id) -> booking`
- `create_payment(booking_id, amount, method, idempotency_key) -> payment`
- `verify_payment(payment_id) -> payment_status`
- `request_refund(payment_id, reason, idempotency_key) -> refund_status`

The demo uses in-memory state and a simulated successful payment. Replace the functions with authenticated calls to real backend services before any real-world use.
