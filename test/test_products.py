from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
import pytest

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse = True)
def clean_database():
    Base.metadata.drop_all(bind = test_engine)
    Base.metadata.create_all(bind = test_engine)
    yield

app.dependency_overrides[get_db] = override_get_db
Base.metadata.create_all(bind=test_engine)
client = TestClient(app)

def test_get_products():
    response = client.get("/products/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_product_not_found():
    response = client.get("/products/999")
    assert response.status_code == 404

def test_create_product_unauthorized():
    response = client.post("/products/", json={
        "name": "Test Product",
        "description": "Test",
        "price": 9.99,
        "stock_quantity": 10,
        "category_id": 1
    })
    assert response.status_code == 401

def test_get_single_product_not_found():
    response = client.get("/products/9999")
    assert response.status_code == 404

def test_create_product_as_non_admin():
    # register regular user
    client.post("/auth/register", json={
        "name": "Regular User",
        "email": "regular@test.com",
        "password": "testpass123"
    })
    login = client.post("/auth/login", json={
        "email": "regular@test.com",
        "password": "testpass123"
    })
    token = login.json()["access_token"]
    response = client.post("/products/",
        json={
            "name": "Test Product",
            "description": "Test",
            "price": 9.99,
            "stock_quantity": 10,
            "category_id": 1
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403

def test_create_product_as_admin():
    # create admin directly in test database
    db = TestingSessionLocal()
    from app.models import User, Category
    from app.routes.auth import hash_password
    
    # create admin user
    admin = User(
        name="Admin",
        email="admin2@test.com",
        hashed_password=hash_password("adminpass"),
        is_admin=True
    )
    db.add(admin)
    
    # create category first since product needs one
    category = Category(name="Test Category", description="Test")
    db.add(category)
    db.commit()
    db.close()
    
    # login as admin
    login = client.post("/auth/login", json={
        "email": "admin2@test.com",
        "password": "adminpass"
    })
    token = login.json()["access_token"]
    
    # create product
    response = client.post("/products/",
        json={
            "name": "Admin Product",
            "description": "Created by admin",
            "price": 29.99,
            "stock_quantity": 100,
            "category_id": 1
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Admin Product"
    
def test_register_user():
    response = client.post("/auth/register", json={
        "name": "Test User",
        "email": "test@test.com",
        "password": "testpass123"
    })
    assert response.status_code == 200
    assert response.json()["email"] == "test@test.com"

def test_login_user():
    client.post("/auth/register", json={
        "name": "Test User",
        "email": "test2@test.com",
        "password": "testpass123"
    })
    response = client.post("/auth/login", json={
        "email": "test2@test.com",
        "password": "testpass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_wrong_password():
    client.post("/auth/register", json={
        "name": "Test User",
        "email": "test3@test.com",
        "password": "testpass123"
    })
    response = client.post("/auth/login", json={
        "email": "test3@test.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401