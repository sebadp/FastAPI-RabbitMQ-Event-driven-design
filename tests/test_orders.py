import pytest

from app.models.database import SessionLocal
from app.models.product_model import Product

db = SessionLocal()
new_product = Product(name="Test Product", price=10.0, stock=100)
db.add(new_product)
db.commit()
db.refresh(new_product)
db.close()

print(f"✅ Created test product with ID {new_product.id}")


def test_create_order(client):
    """Test para crear una orden"""
    # Create a product first
    product = client.post(
        "/api/products/",
        json={"name": "Monitor", "description": "4K Monitor", "price": 300, "stock": 5},
    )
    product_data = product.json()
    product_id = product_data["id"]

    # Create an order with the newly created product using the new format
    response = client.post(
        "/api/orders/", json={"items": [{"item_id": product_id, "quantity": 1}]}
    )

    # Changed from 200 to 201 to match our status_code setting
    assert response.status_code == 201
    assert response.json()["message"] == "Order created successfully"
    assert "order_id" in response.json()
    assert "total_price" in response.json()


def test_pay_order(client):
    """Test para pagar una orden"""
    # First create an order
    product = client.post(
        "/api/products/",
        json={
            "name": "Keyboard",
            "description": "Mechanical Keyboard",
            "price": 100,
            "stock": 10,
        },
    )
    product_data = product.json()
    product_id = product_data["id"]

    # Create the order
    order_response = client.post(
        "/api/orders/", json={"items": [{"item_id": product_id, "quantity": 2}]}
    )
    order_id = order_response.json()["order_id"]

    # Pay the order
    response = client.post(f"/api/orders/{order_id}/pay")

    assert response.status_code == 200
    assert response.json()["message"] == "Order successfully marked as paid"
    assert response.json()["status"] == "paid"


def test_ship_order(client):
    """Test para enviar una orden"""
    # First create and pay an order
    product = client.post(
        "/api/products/",
        json={"name": "Mouse", "description": "Gaming Mouse", "price": 50, "stock": 15},
    )
    product_data = product.json()
    product_id = product_data["id"]

    # Create the order
    order_response = client.post(
        "/api/orders/", json={"items": [{"item_id": product_id, "quantity": 1}]}
    )
    order_id = order_response.json()["order_id"]

    # Pay the order
    client.post(f"/api/orders/{order_id}/pay")

    # Ship the order
    response = client.post(
        f"/api/orders/{order_id}/ship",
        json={"carrier": "FedEx", "tracking_number": "FX123456789US"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Order successfully marked as shipped"
    assert response.json()["status"] == "shipped"
    assert response.json()["tracking_info"]["carrier"] == "FedEx"
