import os
import random
from faker import Faker
from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from app.models.product_model import Product
from app.models.order_model import Order, LineItem
from app.config import logger

fake = Faker()

NUM_PRODUCTS = int(os.getenv("NUM_PRODUCTS", 10))
NUM_ORDERS = int(os.getenv("NUM_ORDERS", 5))
MAX_LINE_ITEMS_PER_ORDER = 3


def seed_products(db: Session, count: int):
    logger.info(f"🌱 Seeding {count} products...")
    for _ in range(count):
        product = Product(
            name=fake.unique.word().capitalize(),
            description=fake.sentence(),
            price=round(random.uniform(5.0, 100.0), 2),
            stock=random.randint(10, 100),
        )
        db.add(product)
    db.commit()
    logger.info("✅ Products seeded.")


def seed_orders(db: Session, count: int):
    products = db.query(Product).all()
    if not products:
        logger.warning("❌ No products found. Seed products first.")
        return

    logger.info(f"📦 Seeding {count} orders...")
    for _ in range(count):
        order = Order()
        db.add(order)
        db.commit()
        db.refresh(order)

        num_line_items = random.randint(1, MAX_LINE_ITEMS_PER_ORDER)
        sampled_products = random.sample(products, min(num_line_items, len(products)))

        for product in sampled_products:
            quantity = random.randint(1, 5)
            line_item = LineItem(
                order_id=order.id, product_id=product.id, quantity=quantity
            )
            db.add(line_item)

        db.commit()

    logger.info("✅ Orders seeded.")


if __name__ == "__main__":
    db: Session = SessionLocal()
    seed_products(db, NUM_PRODUCTS)
    seed_orders(db, NUM_ORDERS)
    db.close()
