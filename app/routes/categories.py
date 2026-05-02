from fastapi import APIRouter, Depends, HTTPException
from app.pydantic_schemas import CategoryCreate, CategoryResponse, CategoryUpdate
from app.database import get_db
from sqlalchemy.orm import Session
from app.models import Category, User
from app.dependencies import get_current_user
from typing import List

router = APIRouter()

@router.post("/", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admins only")
    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Category already exists")
    new_category = Category(name = category.name, description = category.description, parent_id = category.parent_id)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

# GET / — get all categories (public)
@router.get("/", response_model=List[CategoryResponse])
def get_all_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

# GET /{category_id} — get one category (public)
@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

# PUT /{category_id} — update a category (admin only)
@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, category: CategoryUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. Admin check
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # 2. Find the category
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # 3. Only update fields that were actually sent
    update_data = category.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)
    
    # 4. Save
    db.commit()
    db.refresh(db_category)
    return db_category
    

# DELETE /{category_id} — delete a category (admin only)
@router.delete("/{category_id}", response_model=CategoryResponse)
def delete_category(category_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Admin check
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()
    return category
   