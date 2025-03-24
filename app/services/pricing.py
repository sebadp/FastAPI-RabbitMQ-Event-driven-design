from abc import ABC, abstractmethod
from decimal import Decimal


class PricingStrategy(ABC):
    """Abstract base class for pricing strategies"""

    @abstractmethod
    def calculate(self, order):
        pass


class StandardPricing(PricingStrategy):
    """Standard pricing strategy (no discount, no taxes)"""

    def calculate(self, order):
        total = sum(
            line_item.product.price * line_item.quantity
            for line_item in order.line_items
        )
        return total


class TaxedPricing(PricingStrategy):
    """Pricing strategy that applies a fixed tax percentage"""

    def __init__(self, tax_rate=0.1):
        self.tax_rate = Decimal(str(tax_rate))

    def calculate(self, order):
        subtotal = sum(
            line_item.product.price * line_item.quantity
            for line_item in order.line_items
        )
        tax = subtotal * self.tax_rate
        return subtotal + tax


class DiscountPricing(PricingStrategy):
    """Pricing strategy that applies a discount if total exceeds a threshold"""

    def __init__(self, discount_threshold=100, discount_rate=0.1):
        self.discount_threshold = discount_threshold
        self.discount_rate = Decimal(str(discount_rate))

    def calculate(self, order):
        subtotal = sum(
            line_item.product.price * line_item.quantity
            for line_item in order.line_items
        )
        if subtotal > self.discount_threshold:
            discount = subtotal * self.discount_rate
            return subtotal - discount
        return subtotal
