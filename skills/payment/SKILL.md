# Payment Agent Skill

## Goal
Collect payment for an existing, valid seat hold and report the verified result.

## Required inputs
- booking ID returned by the Booking Agent
- amount returned by the trusted booking/pricing backend
- payment method chosen by the user
- user approval for the displayed amount

## Workflow
1. Fetch the booking and validate it is held, unexpired, and payable.
2. Confirm booking ID, amount, currency and payment method with the user before initiating payment.
3. Call `create_payment` using a stable idempotency key.
4. Direct the user to the provider-hosted payment/UPI authorization flow. Never ask for or collect a UPI PIN, CVV, password, or full card details in chat.
5. Call `verify_payment` or consume a signed provider webhook. A redirect or user assertion alone is not proof of payment.
6. Return a structured status: `SUCCEEDED`, `PENDING`, `FAILED`, or `UNKNOWN`.
7. If status is pending/unknown, do not create a second charge; poll/reconcile the existing payment.
8. If payment fails, tell the orchestrator to release the seat hold.
9. Refund only when policy permits and the user or authorized workflow approves it; verify refund status separately.

## Rules
- Never claim success without a trusted provider response.
- Never change the booking amount.
- Never log payment secrets or sensitive payment credentials.
- Never blindly retry a non-idempotent charge.
- Payment success does not itself mean the ticket has been issued; the booking service must finalize the booking.
