from fastapi import APIRouter, Depends, HTTPException
from app.pydantic_schemas import ProductCreate, ProductResponse, ProductUpdate
from app.database import get_db
from sqlalchemy.orm import Session
from app.models import Product, User, Category
from app.dependencies import get_current_user
from typing import List, Optional

router = APIRouter()

# POST / — create a product (admin only)
@router.post("/", response_model=ProductResponse)
def create_products(product: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admins only")
    category = db.query(Category).filter(Category.id == product.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category was not found")
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
    return new_product

# GET / — get all products (public) with optional query parameters for search, category, and sort
@router.get("/", response_model=List[ProductResponse])
def get_products(search: Optional[str] = None, category_id: Optional[int] = None, sort: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Product)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    return query.all()

# GET /{product_id} — get one product (public)
@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# PUT /{product_id} — update a product (admin only)
@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product: ProductUpdate, product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admins only")
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    update_data = product.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
    db.commit()
    db.refresh(db_product)
    return db_product   

# DELETE /{product_id} — delete a product (admin only)
@router.delete("/{product_id}", response_model=ProductResponse)
def delete_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admins only")
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return product