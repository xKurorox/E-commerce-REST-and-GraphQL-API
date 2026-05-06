from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Cart, Order, OrderItem, CartItem, Product
from app.dependencies import get_current_user
import stripe
import os
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
router = APIRouter()

@router.post("/")
def payment(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not user_cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    items = user_cart.cart_items
    if not items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    # Calculate total by multiplying each item's current price by its quantity
    total = sum(item.product.price * item.quantity for item in items)
    # Create a PaymentIntent with Stripe; the client uses the client_secret to confirm payment on the frontend
    payment_intent = stripe.PaymentIntent.create(
        amount=int(total * 100),  # Stripe expects amount in cents
        currency="usd",
        metadata={"user_id": str(user.id)},
        automatic_payment_methods={"enabled": True, "allow_redirects": "never"}
    )
    return {"client_secret": payment_intent.client_secret}

@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    # Verify the request actually came from Stripe using the webhook signature
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        user_id = int(payment_intent["metadata"]["user_id"])
        # Fetch the user's cart and items
        cart = db.query(Cart).filter(Cart.user_id == user_id).first()
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")
        items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
        total = sum(item.product.price * item.quantity for item in items)
        # Create the order record
        order = Order(user_id=user_id, total_amount=total, status="complete",
                      shipping_address="myhome123", payment_status="Paid")
        db.add(order)
        # flush writes to the DB without committing so we get order.id for the order items
        db.flush()
        # Create one OrderItem per cart item
        for item in items:
            order_item = OrderItem(order_id=order.id, product_id=item.product_id,
                                   quantity=item.quantity, unit_price=item.product.price)
            db.add(order_item)
        # Deduct purchased quantities from stock
        for item in items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                setattr(product, "stock_quantity", product.stock_quantity - item.quantity)
                db.add(product)
        # Clear the cart now that the order is placed
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
        db.commit()

    return {"status": "ok"}
