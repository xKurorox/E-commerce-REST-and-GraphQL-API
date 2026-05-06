from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

# --- Auth ---

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_admin: bool
    created_at: datetime
    # from_attributes=True lets Pydantic read data from SQLAlchemy objects, not just dicts
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Categories ---

class CategoryCreate(BaseModel):
    name: str
    description: str
    parent_id: Optional[int] = None

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Products ---

class ProductCreate(BaseModel):
    category_id: int
    name: str
    description: str
    status: Optional[str] = "active"
    price: float
    stock_quantity: int

class ProductUpdate(BaseModel):
    category_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None

class ProductResponse(BaseModel):
    id: int
    category_id: int
    name: str
    description: str
    price: float
    stock_quantity: int
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Cart ---

# Sent by the client when adding a product to the cart
class CartItemCreate(BaseModel):
    product_id: int
    quantity: int

# Sent by the client when changing the quantity of an existing cart item
class CartItemUpdate(BaseModel):
    quantity: int

class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Returns the full cart with all its items nested inside
class CartResponse(BaseModel):
    id: int
    user_id: int
    cart_items: List[CartItemResponse] = []
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Orders ---

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Nested list of all items that belong to this order
class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: str
    shipping_address: str
    payment_status: str
    created_at: datetime
    updated_at: datetime
    order_items: List[OrderItemResponse] = []
    model_config = ConfigDict(from_attributes=True)
