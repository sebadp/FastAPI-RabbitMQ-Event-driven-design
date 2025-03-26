from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.database import Base


class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))  # 🔄 antes era item_id
    quantity = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="line_items")
    product = relationship("Product")  # 🔄 antes era item
