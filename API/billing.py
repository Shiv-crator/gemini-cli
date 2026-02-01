# api/billing.py
# Stripe integration endpoints: create a subscription (demo) and webhook handler.
# IMPORTANT: Use STRIPE test keys for development. DO NOT commit secrets.

import os
import logging
import secrets
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
import stripe

# Import your DB session factory and models
# from .db import SessionLocal
# from .models import Plan, Tenant

# We'll expect the FastAPI app to attach SessionLocal on startup as app.state.SessionLocal
# In the router handlers below, we will get session via request.app.state.SessionLocal()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", None)
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", None)

router = APIRouter(prefix="/billing", tags=["billing"])
logger = logging.getLogger("billing")
logger.setLevel(logging.INFO)


@router.post("/create_subscription")
async def create_subscription(payload: dict, request: Request):
    """
    Demo endpoint to create a tenant + Stripe subscription.
    Body example: { "tenant_name": "acme", "plan_id": 2 }
    Returns the created tenant_id and generated api_key.
    """
    tenant_name = payload.get("tenant_name")
    plan_id = payload.get("plan_id")
    if not tenant_name or not plan_id:
        raise HTTPException(status_code=400, detail="tenant_name and plan_id required")

    SessionLocal = request.app.state.SessionLocal
    session: Session = SessionLocal()
    try:
        # Import models locally to avoid circular imports
        from .models import Plan, Tenant

        plan = session.query(Plan).get(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="plan not found")

        if stripe.api_key is None:
            raise HTTPException(status_code=500, detail="Stripe not configured (STRIPE_SECRET_KEY)")

        # Create Stripe customer
        customer = stripe.Customer.create(name=tenant_name)

        # Create a subscription using inline price_data (DEMO).
        # Production: create Price objects in Stripe dashboard and store price_id in DB.
        sub = stripe.Subscription.create(
            customer=customer["id"],
            items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": plan.name},
                    "unit_amount": int(plan.monthly_price_cents),
                    "recurring": {"interval": "month"}
                }
            }],
            expand=["latest_invoice.payment_intent"]
        )

        # Persist tenant with an API key
        api_key = secrets.token_hex(16)
        tenant = Tenant(name=tenant_name, api_key=api_key, stripe_customer_id=customer["id"], plan_id=plan.id)
        session.add(tenant)
        session.commit()

        return {"tenant_id": tenant.id, "api_key": api_key, "stripe_subscription_id": sub["id"]}

    finally:
        session.close()


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Webhook receiver. Configure the STRIPE_WEBHOOK_SECRET in your env.
    Map Stripe events to tenant state (payment succeeded/failed, canceled).
    """
    if WEBHOOK_SECRET is None:
        raise HTTPException(status_code=500, detail="Stripe webhook secret not configured")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except ValueError as e:
        logger.exception("Invalid payload")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.exception("Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle relevant events
    event_type = event["type"]
    logger.info("Received Stripe event: %s", event_type)

    # Basic mapping (extend as needed)
    if event_type == "invoice.payment_succeeded":
        # mark tenant active / clear billing flags / generate invoice records
        logger.info("Invoice payment succeeded")
    elif event_type == "invoice.payment_failed":
        # mark tenant billing problem / reduce quota / notify
        logger.info("Invoice payment failed")
    elif event_type == "customer.subscription.deleted":
        logger.info("Subscription canceled")
    # Add more event types as needed

    return {"status": "ok"}
