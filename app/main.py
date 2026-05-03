from fastapi import FastAPI, Depends
from strawberry.fastapi import GraphQLRouter
from app.graphql.schema import schema
from app.database import engine, Base
from app import models
from app.routes.auth import router as auth_router
from app.routes.products import router as products_router
from app.routes.categories import router as categories_router
from app.database import get_db

async def get_context(db=Depends(get_db)):
    return {"db": db}

graphql_app = GraphQLRouter(schema, context_getter=get_context)
app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(products_router, prefix="/products")
app.include_router(categories_router, prefix="/categories")
app.include_router(auth_router, prefix="/auth")
app.include_router(graphql_app, prefix="/graphql")