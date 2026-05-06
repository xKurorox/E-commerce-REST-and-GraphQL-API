from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Order, OrderItem, User
from app.dependencies import get_current_user
from app.pydantic_schemas import OrderItemResponse, OrderResponse
from typing import List

router = APIRouter()

@router.get("/", response_model=List[OrderResponse])
def get_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Load orders via the relationship instead of a separate query
    return user.orders

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Filter by user_id as well so users can't fetch other people's orders
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
