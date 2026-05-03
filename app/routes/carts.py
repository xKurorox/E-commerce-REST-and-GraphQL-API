from fastapi import APIRouter, Depends, HTTPException
from app.pydantic_schemas import CartItemCreate, CartItemResponse, CartItemUpdate, CartResponse
from app.database import get_db
from sqlalchemy.orm import Session
from app.models import User, Product, CartItem, Cart
from app.dependencies import get_current_user
from typing import List

router = APIRouter()

# GET /cart — get the current user's cart and all its items
@router.get("/", response_model=CartResponse)
def user_cart(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart

# POST /cart/items — add a product to the cart
@router.post("/items", response_model=CartItemResponse)
def add_item(item: CartItemCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing_item = db.query(Product).filter(Product.id == item.product_id).first()
    if not existing_item:
        raise HTTPException(status_code=404, detail="Product not found")
    if existing_item.stock_quantity < item.quantity:
        raise HTTPException(status_code=409, detail="Not enough product in stock")
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    existing_cart_item = db.query(CartItem).filter(CartItem.product_id == item.product_id, CartItem.cart_id == cart.id).first()
    if existing_cart_item:
        existing_cart_item.quantity += item.quantity
        db.commit()
        db.refresh(existing_cart_item)
        return existing_cart_item
    else:
        new_cart_item = CartItem(cart_id = cart.id, product_id = item.product_id, quantity = item.quantity)
        db.add(new_cart_item)
        db.commit()
        db.refresh(new_cart_item)
        return new_cart_item

# PUT /cart/items/{item_id} — update quantity of a cart item
@router.put("/items/{item_id}", response_model=CartItemResponse)
def update_cart_item(item_id: int, quantity: CartItemUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    existing_cart_item = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.product_id == item_id).first()
    if not existing_cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    product = db.query(Product).filter(Product.id == existing_cart_item.product_id).first()
    if product.stock_quantity < quantity.quantity:
        raise HTTPException(status_code=409, detail="Not enough product in stock")
    existing_cart_item.quantity = quantity.quantity
    db.commit()
    db.refresh(existing_cart_item)
    return existing_cart_item

# DELETE /cart/items/{item_id} — remove an item from the cart
@router.delete("/items/{item_id}", response_model=CartItemResponse)
def delete_cart_item(item_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    cart_item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(cart_item)
    db.commit()
    return cart_item
