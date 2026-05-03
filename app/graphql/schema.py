import strawberry
from strawberry.types import Info
from typing import Optional
from app.models import Category as DBCategory
from app.models import Product as DBProduct

@strawberry.type
class Category:
    id: int
    name: str
    description: str
    parent_id: Optional[int] = None

@strawberry.type
class Product:
    id: int
    name: str
    description: str
    price: float
    stock_quantity: int
    status: str
    category_id: int

@strawberry.type
class Query:
    @strawberry.field
    def categories(self, info: Info) -> list[Category]:
        db = info.context["db"]
        db_categories = db.query(DBCategory).all()
        return [Category(id=c.id, name=c.name, description=c.description) for c in db_categories]

    @strawberry.field
    def category(self, info: Info, id: int) -> Optional[Category]:
        db = info.context["db"]
        db_category = db.query(DBCategory).filter(DBCategory.id == id).first()
        if not db_category:
            return None
        return Category(id=db_category.id, name=db_category.name, description=db_category.description, 
                        parent_id=db_category.parent_id)

    @strawberry.field
    def products(self, info: Info) -> list[Product]:
        db = info.context["db"]
        db_products = db.query(DBProduct).all()
        return [Product(id=c.id, name=c.name, description=c.description, price=c.price,
                        stock_quantity=c.stock_quantity, status=c.status, category_id=c.category_id) 
                        for c in db_products]

    @strawberry.field
    def product(self, info: Info, id: int) -> Optional[Product]:
        db = info.context["db"]
        db_product = db.query(DBProduct).filter(DBProduct.id == id).first()
        if not db_product:
            return None
        return Product(id=db_product.id, name=db_product.name, description=db_product.description, 
                       price=db_product.price, stock_quantity=db_product.stock_quantity, status=db_product.status, 
                       category_id=db_product.category_id)
schema = strawberry.Schema(query=Query)