from fastapi import APIRouter, Depends, HTTPException
from app.pydantic_schemas import ProductCreate, ProductResponse, ProductUpdate
from app.database import get_db
from sqlalchemy.orm import Session
from app.models import Product, User, Category
from app.dependencies import get_current_user
from typing import List, Optional
from app.routes.redis_client import redis_client
import json

router = APIRouter()

@router.post("/", response_model=ProductResponse)
def create_products(product: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admins only")
    # Make sure the category exists before creating a product under it
    category = db.query(Category).filter(Category.id == product.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category was not found")
    # Block duplicate product names
    existing_product = db.query(Product).filter(Product.name == product.name).first()
    if existing_product:
        raise HTTPException(status_code=409, detail="Product already exist")
    new_product = Product(category_id = product.category_id,
                          name = product.name,
                          description = product.description,
                          status = product.status,
                          price = product.price,
                          stock_quantity = product.stock_quantity)
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    redis_client.delete("products:search=None:category=None:sort=None")
    return new_product

@router.get("/", response_model=List[ProductResponse])
def get_products(search: Optional[str] = None, category_id: Optional[int] = None, sort: Optional[str] = None, db: Session = Depends(get_db)):
    # Build a unique cache key from the query parameters so different filter combinations are cached separately
    cache_key = f"products:search={search}:category={category_id}:sort={sort}"
    cached = redis_client.get(cache_key)
    if cached:
        # Deserialize the cached JSON string and reconstruct Pydantic models to keep response validation intact
        return [ProductResponse(**p) for p in json.loads(cached)]
    query = db.query(Product)
    if search:
        # ilike is case-insensitive LIKE search
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    products = query.all()
    # Serialize to JSON-safe dicts before storing; mode="json" handles datetime fields automatically
    products_data = [ProductResponse.model_validate(p).model_dump(mode="json") for p in products]
    redis_client.setex(cache_key, 60, json.dumps(products_data))
    return products

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    cache_key = f"product:{product_id}"
    cached = redis_client.get(cache_key)
    if cached:
        # Return the cached dict directly; FastAPI serializes it via the response_model
        return json.loads(cached)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    # Convert to Pydantic then to a JSON-safe dict so datetimes serialize correctly
    product_data = ProductResponse.model_validate(product).model_dump(mode="json")
    # setex stores the value with an expiry of 60 seconds in a single call
    redis_client.setex(cache_key, 60, json.dumps(product_data))
    return product

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product: ProductUpdate, product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admins only")
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    # exclude_unset=True means only fields the client actually sent are updated, leaving the rest unchanged
    update_data = product.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
    db.commit()
    db.refresh(db_product)
    # Invalidate the individual product cache and all list caches since data has changed
    redis_client.delete(f"product:{product_id}")
    redis_client.delete("products:search=None:category=None:sort=None") 
    return db_product   

@router.delete("/{product_id}", response_model=ProductResponse)
def delete_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admins only")
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    # Invalidate the individual product cache and all list caches
    redis_client.delete(f"product:{product_id}")
    redis_client.delete("products:search=None:category=None:sort=None")
    return product
