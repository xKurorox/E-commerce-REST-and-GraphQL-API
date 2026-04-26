import strawberry

@strawberry.type
class Product:
    name: str

@strawberry.type
class Query:
    @strawberry.field
    def product(self) -> Product:
        return Product(name="Hello world")
    
schema = strawberry.Schema(query=Query)