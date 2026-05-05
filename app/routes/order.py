from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Order, OrderItem, User
from app.dependencies import get_current_user
from app.pydantic_schemas import OrderItemResponse, OrderResponse
from typing import List

router = APIRouter()

# GET /orders — get all orders for the current user
@router.get("/", response_model=List[OrderResponse])
def get_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = user.orders
    return orders

# GET /orders/{order_id} — get a single order with its items
@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order