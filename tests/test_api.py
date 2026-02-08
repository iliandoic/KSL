import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from database.connection import Base, get_db
from main import app

# Create test DB with StaticPool for thread safety
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=test_engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create all tables in test DB
Base.metadata.create_all(test_engine)

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "KSL API"


def test_syllables():
    response = client.post("/api/syllables", json={"line": "Имам пари да хвърлям"})
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 7


def test_syllables_missing_field():
    response = client.post("/api/syllables", json={})
    assert response.status_code == 422


def test_rhymes():
    response = client.post("/api/rhymes", json={"word": "пари"})
    assert response.status_code == 200
    data = response.json()
    assert "perfect" in data
    assert "near" in data
    assert "slant" in data


def test_rhymes_missing_field():
    response = client.post("/api/rhymes", json={})
    assert response.status_code == 422


def test_corpus_ingest():
    response = client.post("/api/corpus/ingest", json={
        "text": "Имам пари да хвърлям\nКарам мерцедес по булеварда",
        "source": "test"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["lines_added"] > 0


def test_corpus_search():
    # First ingest something with money theme keywords
    client.post("/api/corpus/ingest", json={
        "text": "Пари в джоба, злато на врата",
        "source": "test"
    })
    response = client.post("/api/corpus/search", json={"theme": "money"})
    assert response.status_code == 200
    data = response.json()
    assert "lines" in data


def test_corpus_ingest_empty():
    response = client.post("/api/corpus/ingest", json={"text": ""})
    assert response.status_code == 200
    data = response.json()
    assert data["lines_added"] == 0


def test_style_import():
    response = client.post("/api/style/import", json={
        "text": "Имам пари да хвърлям\nЖивотът е купон",
        "mode": "my_lyrics"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@patch("routers.complete.complete_lines")
def test_complete(mock_complete):
    mock_complete.return_value = ["Пари в джоба", "Злато на врата"]
    response = client.post("/api/complete", json={
        "lines": ["Имам пари да хвърлям"],
        "theme": "money"
    })
    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data


@patch("routers.spark.generate_titles")
def test_spark_titles(mock_titles):
    mock_titles.return_value = ["Заглавие 1", "Заглавие 2"]
    response = client.post("/api/spark/titles", json={"theme": "money"})
    assert response.status_code == 200
    data = response.json()
    assert "titles" in data


@patch("routers.spark.random_spark")
def test_spark_random(mock_random):
    mock_random.return_value = {"spark": "Нещо интересно", "type": "line"}
    response = client.post("/api/spark/random")
    assert response.status_code == 200
    data = response.json()
    assert "spark" in data
    assert "type" in data


@patch("routers.spark.word_explosion")
def test_spark_explode(mock_explode):
    mock_explode.return_value = {
        "starts_with": ["Нощта е моя"],
        "ends_with": ["Сам в тази нощ"],
        "rhymes": ["мощ"],
        "combos": ["нощен крал"],
    }
    response = client.post("/api/spark/explode", json={"word": "нощ"})
    assert response.status_code == 200
    data = response.json()
    assert "starts_with" in data
    assert "ends_with" in data
    assert "rhymes" in data
    assert "combos" in data
