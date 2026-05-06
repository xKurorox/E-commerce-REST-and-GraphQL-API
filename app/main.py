from fastapi import FastAPI, Depends
from strawberry.fastapi import GraphQLRouter
from app.graphql.schema import schema
from app.database import engine, Base, get_db
from app import models
from app.routes.auth import router as auth_router
from app.routes.products import router as products_router
from app.routes.categories import router as categories_router
from app.routes.carts import router as carts_router
from app.routes.checkout import router as checkout_router
from app.routes.order import router as order_router

app = FastAPI()

# Injects the database session into every GraphQL request via info.context["db"]
async def get_context(db=Depends(get_db)):
    return {"db": db}

# Wrap the Strawberry schema in a FastAPI router; exposes POST /graphql and GET /graphql (GraphiQL)
graphql_app = GraphQLRouter(schema, context_getter=get_context)

# Create all database tables if they don't already exist
Base.metadata.create_all(bind=engine)

# Register all REST routers with their URL prefixes
app.include_router(products_router, prefix="/products")
app.include_router(categories_router, prefix="/categories")
app.include_router(auth_router, prefix="/auth")
app.include_router(graphql_app, prefix="/graphql")
app.include_router(carts_router, prefix="/carts")
app.include_router(checkout_router, prefix="/checkout")
app.include_router(order_router, prefix="/orders")
