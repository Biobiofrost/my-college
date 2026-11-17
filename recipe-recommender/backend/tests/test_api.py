import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register():
    response = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"


def test_login():
    client.post("/api/auth/register", json={
        "username": "loginuser",
        "email": "login@example.com",
        "password": "testpassword"
    })

    response = client.post("/api/auth/login", data={
        "username": "loginuser",
        "password": "testpassword"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_get_recipes():
    response = client.get("/api/recipes/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_recipe_by_id():
    response = client.get("/api/recipes/1")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "ingredients" in data
    assert "steps" in data


def test_search_recipes():
    response = client.get("/api/recipes/?search=红烧")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_profile():
    register_response = client.post("/api/auth/register", json={
        "username": "profileuser",
        "email": "profile@example.com",
        "password": "testpassword"
    })

    login_response = client.post("/api/auth/login", data={
        "username": "profileuser",
        "password": "testpassword"
    })
    token = login_response.json()["access_token"]

    response = client.put(
        "/api/users/profile",
        json={
            "hometown": "四川",
            "current_city": "北京",
            "taste_preferences": {"spicy": 0.8, "sweet": 0.3}
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["hometown"] == "四川"
    assert data["current_city"] == "北京"


def test_submit_state():
    register_response = client.post("/api/auth/register", json={
        "username": "stateuser",
        "email": "state@example.com",
        "password": "testpassword"
    })

    login_response = client.post("/api/auth/login", data={
        "username": "stateuser",
        "password": "testpassword"
    })
    token = login_response.json()["access_token"]

    response = client.post(
        "/api/users/state",
        json={
            "body_feeling": "感觉干燥",
            "mood": "想吃点辣的",
            "craving": "火锅"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "id" in response.json()


def test_get_recommendations():
    register_response = client.post("/api/auth/register", json={
        "username": "recuser",
        "email": "rec@example.com",
        "password": "testpassword"
    })

    login_response = client.post("/api/auth/login", data={
        "username": "recuser",
        "password": "testpassword"
    })
    token = login_response.json()["access_token"]

    client.post(
        "/api/users/state",
        json={"craving": "红烧肉"},
        headers={"Authorization": f"Bearer {token}"}
    )

    response = client.get(
        "/api/recommend/today?limit=5",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_search_by_ingredients():
    response = client.get("/api/recipes/search/by-ingredients?ingredients=豆腐,肉末")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
