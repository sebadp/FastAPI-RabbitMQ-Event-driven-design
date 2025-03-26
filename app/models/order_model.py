import enum

from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.database import Base
from datetime import datetime


class OrderStatus(enum.Enum):
    CREATED = "created"
    PENDING_PAYMENT = "pending_payment"
    IN_PREPARATION = "in_preparation"
    READY_TO_SHIP = "ready_to_ship"
    SHIPPED = "shipped"
    DELIVERED = "delivered"


class Order(Base):
    """Customer Orders"""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.CREATED, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    tracking_number = Column(String, nullable=True)
    carrier = Column(String, nullable=True)

    # Relationship with LineItem
    line_items = relationship("LineItem", back_populates="order")

    def calculate_total(self, pricing_strategy):
        """Calculates the total price using a pricing strategy"""
        return pricing_strategy.calculate(self)

    def mark_as_paid(self):
        """Mark the order as paid"""
        self.status = OrderStatus.PENDING_PAYMENT

    def mark_as_shipped(self):
        """Mark the order as shipped"""
        self.status = OrderStatus.SHIPPED

    def mark_as_delivered(self):
        """Mark the order as delivered"""
        self.status = OrderStatus.DELIVERED
