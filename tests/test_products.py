import pytest


def test_create_product(client):
    """Test para agregar un nuevo producto"""
    response = client.post(
        "/api/products/",
        json={
            "name": "Laptop",
            "description": "Gaming Laptop",
            "price": 1200,
            "stock": 10,
        },
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Laptop"


def test_list_products(client):
    """Test para listar productos"""
    response = client.get("/api/products/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_product(client):
    """Test para obtener detalles de un producto"""
    product = client.post(
        "/api/products/",
        json={
            "name": "Mouse",
            "description": "Wireless Mouse",
            "price": 50,
            "stock": 100,
        },
    ).json()

    product_id = product["id"]
    response = client.get(f"/api/products/{product_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Mouse"


def test_update_product(client):
    """Test para actualizar información de un producto"""

    product = client.post(
        "/api/products/",
        json={
            "name": "Keyboard",
            "description": "Mechanical Keyboard",
            "price": 80,
            "stock": 50,
        },
    ).json()

    product_id = product["id"]
    response = client.put(
        f"/api/products/{product_id}",
        json={
            "name": "Mechanical Keyboard",
            "description": "Updated Keyboard",
            "price": 90,
            "stock": 40,
        },
    )
    assert response.status_code == 200
    assert response.json()["price"] == 90
