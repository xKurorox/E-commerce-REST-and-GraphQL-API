from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import User, Category, Product
from app.routes.auth import hash_password
import pytest

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_carts.db"
test_engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield

app.dependency_overrides[get_db] = override_get_db
Base.metadata.create_all(bind=test_engine)
client = TestClient(app)

def seed_product():
    db = TestingSessionLocal()
    category = Category(name="Electronics", description="Electronic items")
    db.add(category)
    db.flush()
    product = Product(name="Headphones", description="Wireless", price=49.99, stock_quantity=10, category_id=category.id)
    db.add(product)
    db.commit()
    db.close()

def get_user_token():
    client.post("/auth/register", json={"name": "Test User", "email": "user@test.com", "password": "userpass"})
    login = client.post("/auth/login", json={"email": "user@test.com", "password": "userpass"})
    return login.json()["access_token"]

def test_get_cart_unauthorized():
    response = client.get("/carts/")
    assert response.status_code == 401

def test_get_cart_empty():
    token = get_user_token()
    response = client.get("/carts/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["cart_items"] == []

def test_add_item_unauthorized():
    response = client.post("/carts/items", json={"product_id": 1, "quantity": 1})
    assert response.status_code == 401

def test_add_item_product_not_found():
    token = get_user_token()
    response = client.post("/carts/items",
        json={"product_id": 999, "quantity": 1},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404

def test_add_item_not_enough_stock():
    seed_product()
    token = get_user_token()
    response = client.post("/carts/items",
        json={"product_id": 1, "quantity": 999},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 409

def test_add_item_success():
    seed_product()
    token = get_user_token()
    response = client.post("/carts/items",
        json={"product_id": 1, "quantity": 2},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["product_id"] == 1
    assert response.json()["quantity"] == 2

def test_add_existing_item_increments_quantity():
    seed_product()
    token = get_user_token()
    client.post("/carts/items",
        json={"product_id": 1, "quantity": 2},
        headers={"Authorization": f"Bearer {token}"}
    )
    response = client.post("/carts/items",
        json={"product_id": 1, "quantity": 3},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["quantity"] == 5

def test_update_cart_item():
    seed_product()
    token = get_user_token()
    client.post("/carts/items",
        json={"product_id": 1, "quantity": 2},
        headers={"Authorization": f"Bearer {token}"}
    )
    response = client.put("/carts/items/1",
        json={"quantity": 4},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["quantity"] == 4

def test_update_cart_item_not_found():
    token = get_user_token()
    response = client.put("/carts/items/999",
        json={"quantity": 1},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404

def test_delete_cart_item():
    seed_product()
    token = get_user_token()
    client.post("/carts/items",
        json={"product_id": 1, "quantity": 2},
        headers={"Authorization": f"Bearer {token}"}
    )
    response = client.delete("/carts/items/1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

def test_delete_cart_item_not_found():
    token = get_user_token()
    response = client.delete("/carts/items/999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
