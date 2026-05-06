from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import User, Category
from app.routes.auth import hash_password
import pytest

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_categories.db"
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

def get_admin_token():
    db = TestingSessionLocal()
    admin = User(name="Admin", email="admin@test.com", hashed_password=hash_password("adminpass"), is_admin=True)
    db.add(admin)
    db.commit()
    db.close()
    login = client.post("/auth/login", json={"email": "admin@test.com", "password": "adminpass"})
    return login.json()["access_token"]

def get_user_token():
    client.post("/auth/register", json={"name": "Regular User", "email": "user@test.com", "password": "userpass"})
    login = client.post("/auth/login", json={"email": "user@test.com", "password": "userpass"})
    return login.json()["access_token"]

def test_get_categories_empty():
    response = client.get("/categories/")
    assert response.status_code == 200
    assert response.json() == []

def test_get_category_not_found():
    response = client.get("/categories/999")
    assert response.status_code == 404

def test_create_category_unauthorized():
    response = client.post("/categories/", json={"name": "Electronics", "description": "Electronic items"})
    assert response.status_code == 401

def test_create_category_as_non_admin():
    token = get_user_token()
    response = client.post("/categories/",
        json={"name": "Electronics", "description": "Electronic items"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403

def test_create_category_as_admin():
    token = get_admin_token()
    response = client.post("/categories/",
        json={"name": "Electronics", "description": "Electronic items"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Electronics"

def test_create_duplicate_category():
    token = get_admin_token()
    client.post("/categories/",
        json={"name": "Electronics", "description": "Electronic items"},
        headers={"Authorization": f"Bearer {token}"}
    )
    response = client.post("/categories/",
        json={"name": "Electronics", "description": "Duplicate"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 409

def test_get_category():
    token = get_admin_token()
    client.post("/categories/",
        json={"name": "Electronics", "description": "Electronic items"},
        headers={"Authorization": f"Bearer {token}"}
    )
    response = client.get("/categories/1")
    assert response.status_code == 200
    assert response.json()["name"] == "Electronics"

def test_update_category_as_admin():
    token = get_admin_token()
    client.post("/categories/",
        json={"name": "Electronics", "description": "Electronic items"},
        headers={"Authorization": f"Bearer {token}"}
    )
    response = client.put("/categories/1",
        json={"name": "Updated Electronics"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Electronics"

def test_update_category_not_found():
    token = get_admin_token()
    response = client.put("/categories/999",
        json={"name": "Doesnt Exist"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404

def test_delete_category_as_admin():
    token = get_admin_token()
    client.post("/categories/",
        json={"name": "Electronics", "description": "Electronic items"},
        headers={"Authorization": f"Bearer {token}"}
    )
    response = client.delete("/categories/1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

def test_delete_category_not_found():
    token = get_admin_token()
    response = client.delete("/categories/999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404

def test_delete_category_as_non_admin():
    token = get_admin_token()
    client.post("/categories/",
        json={"name": "Electronics", "description": "Electronic items"},
        headers={"Authorization": f"Bearer {token}"}
    )
    user_token = get_user_token()
    response = client.delete("/categories/1", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403
