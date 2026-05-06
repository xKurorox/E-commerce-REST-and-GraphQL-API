from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import User, Order, OrderItem, Category, Product
from app.routes.auth import hash_password
import pytest

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_orders.db"
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

def get_user_token():
    client.post("/auth/register", json={"name": "Test User", "email": "user@test.com", "password": "userpass"})
    login = client.post("/auth/login", json={"email": "user@test.com", "password": "userpass"})
    return login.json()["access_token"]

def seed_order(user_id: int):
    db = TestingSessionLocal()
    category = Category(name="Electronics", description="Electronic items")
    db.add(category)
    db.flush()
    product = Product(name="Headphones", description="Wireless", price=49.99, stock_quantity=10, category_id=category.id)
    db.add(product)
    db.flush()
    order = Order(user_id=user_id, total_amount=49.99, status="complete", shipping_address="123 Main St", payment_status="Paid")
    db.add(order)
    db.flush()
    order_item = OrderItem(order_id=order.id, product_id=product.id, quantity=1, unit_price=49.99)
    db.add(order_item)
    db.commit()
    db.close()

def test_get_orders_unauthorized():
    response = client.get("/orders/")
    assert response.status_code == 401

def test_get_orders_empty():
    token = get_user_token()
    response = client.get("/orders/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == []

def test_get_orders():
    token = get_user_token()
    seed_order(user_id=1)
    response = client.get("/orders/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["total_amount"] == 49.99

def test_get_single_order():
    token = get_user_token()
    seed_order(user_id=1)
    response = client.get("/orders/1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["id"] == 1

def test_get_single_order_not_found():
    token = get_user_token()
    response = client.get("/orders/999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404

def test_cannot_access_another_users_order():
    token = get_user_token()
    seed_order(user_id=1)
    client.post("/auth/register", json={"name": "Other User", "email": "other@test.com", "password": "otherpass"})
    other_login = client.post("/auth/login", json={"email": "other@test.com", "password": "otherpass"})
    other_token = other_login.json()["access_token"]
    response = client.get("/orders/1", headers={"Authorization": f"Bearer {other_token}"})
    assert response.status_code == 404
