"""Google ADK agent definitions. Tool functions are imported from tools.py."""
from pathlib import Path
from dotenv import load_dotenv
from google.adk.agents import Agent

load_dotenv()
BASE_DIR = Path(__file__).parent


def read_skill(relative_path: str) -> str:
    return (BASE_DIR / relative_path).read_text(encoding="utf-8")


booking_skill = read_skill("skills/booking/SKILL.md")
payment_skill = read_skill("skills/payment/SKILL.md")

from tools import (
    search_shows, check_seats, reserve_seats, get_booking,
    create_payment, verify_payment, request_refund,
)

booking_agent = Agent(
    name="booking_agent",
    model="gemini-2.5-flash",
    description="Finds shows, checks seats, and creates temporary seat holds.",
    instruction=f"""
You are the Booking Agent.
Follow this skill file as policy:
{booking_skill}

Use tools for all live show, seat, price and booking facts. Do not invent results.
Ask for missing fields and explicit user confirmation before reserve_seats.
For this demo, use the authenticated demo user_id 'demo_user' only after user approval.
When a booking is created, return booking_id, show_id, seats, amount, currency and expiry.
Do not initiate payment or say payment succeeded.
""",
    tools=[search_shows, check_seats, reserve_seats, get_booking],
)

payment_agent = Agent(
    name="payment_agent",
    model="gemini-2.5-flash",
    description="Processes and verifies payment for an existing seat hold.",
    instruction=f"""
You are the Payment Agent.
Follow this skill file as policy:
{payment_skill}

Use the booking backend's get_booking result to verify the booking and amount.
Ask for explicit approval before initiating a payment if approval is not already recorded.
Use the amount returned by get_booking, not a user-supplied amount.
Use create_payment and then verify_payment for this demo.
Clearly state that payment is simulated in this POC. Never request a UPI PIN or CVV.
Return payment_id, status, booking_id and ticket_id only when tools return them.
""",
    tools=[get_booking, create_payment, verify_payment, request_refund],
)

root_agent = Agent(
    name="movie_booking_orchestrator",
    model="gemini-2.5-flash",
    description="Coordinates the booking and payment agents for movie ticket purchases.",
    instruction="""
You are the Root Orchestrator for a movie ticket booking POC.
You coordinate exactly two domain agents: booking_agent and payment_agent.

Workflow:
1. Gather movie, theatre, date, preferred showtime, ticket count and payment method.
2. Delegate show search, seat selection and temporary reservation to booking_agent.
3. Before reservation, ensure the user explicitly approved the exact show, seats, total price and cancellation terms.
4. After booking_agent returns a valid HELD booking, delegate payment to payment_agent.
5. Never tell the user a booking is complete based only on a model response. Require tool-backed payment status SUCCEEDED and booking status CONFIRMED.
6. If payment fails, remains pending, or is unknown, communicate that accurately; do not claim confirmation or create a second payment blindly.
7. In this mocked POC, disclose that no real ticket or payment is created.
8. Ask a concise clarification if required details are missing. Never invent availability or prices.
""",
    sub_agents=[booking_agent, payment_agent],
)
