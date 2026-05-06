import strawberry
from strawberry.types import Info
from typing import Optional
# Import SQLAlchemy models aliased to avoid name collision with the Strawberry types below
from app.models import Category as DBCategory
from app.models import Product as DBProduct
from app.models import Order as DBOrder

# Strawberry GraphQL types — these define the shape of data returned to the client

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
class Order:
    id: int
    user_id: int
    total_amount: float
    status: Optional[str] = "Pending"
    shipping_address: str
    payment_status: Optional[str] = "unpaid"

# Query defines all available read operations; each @strawberry.field becomes a queryable field
@strawberry.type
class Query:
    @strawberry.field
    def categories(self, info: Info) -> list[Category]:
        # info.context["db"] is the database session injected via get_context in main.py
        db = info.context["db"]
        db_categories = db.query(DBCategory).all()
        # Map SQLAlchemy objects to Strawberry types before returning
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

# Mutation defines all write operations available over GraphQL
@strawberry.type
class Mutation:
    @strawberry.mutation
    def update_order_status(self, info: Info, order_id: int, status: str) -> Optional[Order]:
        db = info.context["db"]
        db_order = db.query(DBOrder).filter(DBOrder.id == order_id).first()
        if not db_order:
            return None
        db_order.status = status
        db.commit()
        db.refresh(db_order)
        return Order(
            id=db_order.id,
            user_id=db_order.user_id,
            total_amount=db_order.total_amount,
            status=db_order.status,
            shipping_address=db_order.shipping_address,
            payment_status=db_order.payment_status
        )

# Compile the schema — this is what FastAPI uses to serve the GraphQL endpoint
schema = strawberry.Schema(query=Query, mutation=Mutation)
