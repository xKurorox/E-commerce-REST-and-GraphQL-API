from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from app.graphql.schema import schema
from app.database import engine, Base
from app import models
from app.routes.auth import router as auth_router
from app.routes.products import router as products_router
from app.routes.categories import router as categories_router

app = FastAPI()

app.include_router(products_router, prefix="/products")
app.include_router(categories_router, prefix="/categories")
app.include_router(auth_router, prefix="/auth")

Base.metadata.create_all(bind=engine)

graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")