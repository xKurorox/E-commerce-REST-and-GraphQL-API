from fastapi import APIRouter, Depends, HTTPException
from app.pydantic_schemas import CartItemCreate, CartItemResponse, CartItemUpdate, CartResponse
from app.database import get_db
from sqlalchemy.orm import Session
from app.models import User, Product, CartItem, Cart
from app.dependencies import get_current_user
from typing import List

router = APIRouter()

@router.get("/", response_model=CartResponse)
def user_cart(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    # Create an empty cart if the user doesn't have one yet
    if not cart:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart

@router.post("/items", response_model=CartItemResponse)
def add_item(item: CartItemCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Verify the product exists in the catalog
    existing_item = db.query(Product).filter(Product.id == item.product_id).first()
    if not existing_item:
        raise HTTPException(status_code=404, detail="Product not found")
    # Reject if requested quantity exceeds available stock
    if existing_item.stock_quantity < item.quantity:
        raise HTTPException(status_code=409, detail="Not enough product in stock")
    # Get or create the user's cart
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    # If the product is already in the cart, increment instead of creating a duplicate row
    existing_cart_item = db.query(CartItem).filter(CartItem.product_id == item.product_id, CartItem.cart_id == cart.id).first()
    if existing_cart_item:
        existing_cart_item.quantity += item.quantity
        db.commit()
        db.refresh(existing_cart_item)
        return existing_cart_item
    else:
        new_cart_item = CartItem(cart_id=cart.id, product_id=item.product_id, quantity=item.quantity)
        db.add(new_cart_item)
        db.commit()
        db.refresh(new_cart_item)
        return new_cart_item

@router.put("/items/{item_id}", response_model=CartItemResponse)
def update_cart_item(item_id: int, quantity: CartItemUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    # Filter by cart_id as well so users can't update items from other people's carts
    existing_cart_item = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.id == item_id).first()
    if not existing_cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    product = db.query(Product).filter(Product.id == existing_cart_item.product_id).first()
    if product.stock_quantity < quantity.quantity:
        raise HTTPException(status_code=409, detail="Not enough product in stock")
    # Set the quantity directly (not increment) since this is an explicit update
    existing_cart_item.quantity = quantity.quantity
    db.commit()
    db.refresh(existing_cart_item)
    return existing_cart_item

@router.delete("/items/{item_id}", response_model=CartItemResponse)
def delete_cart_item(item_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    # Filter by cart_id so users can only delete their own items
    cart_item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(cart_item)
    db.commit()
    # SQLAlchemy still holds the object in memory after delete so we can return it
    return cart_item
