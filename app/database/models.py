"""SQLAlchemy models for the Business Intelligence database."""

from datetime import datetime, date
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_name = Column(String(120), nullable=False, index=True)
    industry = Column(String(60), nullable=False, index=True)
    region = Column(String(50), nullable=False, index=True)  # North America, EMEA, APAC, LATAM
    tier = Column(String(30), nullable=False, index=True)    # Enterprise, Mid-Market, SMB
    signup_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sales = relationship("Sale", back_populates="customer", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String(120), nullable=False, unique=True, index=True)
    category = Column(String(60), nullable=False, index=True) # SaaS Subscription, Hardware, Services, Security
    unit_price = Column(Float, nullable=False)
    unit_cost = Column(Float, nullable=False)
    target_margin_pct = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)

    sales = relationship("Sale", back_populates="product", cascade="all, delete-orphan")


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_number = Column(String(50), nullable=False, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    order_date = Column(Date, nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)
    discount_pct = Column(Float, default=0.0)
    gross_amount = Column(Float, nullable=False)
    net_amount = Column(Float, nullable=False)
    cogs_amount = Column(Float, nullable=False)
    gross_profit = Column(Float, nullable=False)
    payment_status = Column(String(30), nullable=False, default="Completed", index=True)
    region = Column(String(50), nullable=False, index=True)

    customer = relationship("Customer", back_populates="sales")
    product = relationship("Product", back_populates="sales")

    __table_args__ = (
        Index("idx_sales_date_customer", "order_date", "customer_id"),
        Index("idx_sales_date_product", "order_date", "product_id"),
    )


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    expense_date = Column(Date, nullable=False, index=True)
    category = Column(String(60), nullable=False, index=True) # R&D, Sales & Marketing, G&A, Cloud, Support
    department = Column(String(60), nullable=False, index=True)
    vendor = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    amount = Column(Float, nullable=False)
    payment_status = Column(String(30), nullable=False, default="Paid")

    __table_args__ = (
        Index("idx_expenses_date_cat", "expense_date", "category"),
    )


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=False, index=True)
    quarter = Column(String(10), nullable=False, index=True) # Q1, Q2, Q3, Q4
    month = Column(Integer, nullable=False, index=True)      # 1-12
    category = Column(String(60), nullable=False, index=True)
    department = Column(String(60), nullable=False, index=True)
    budgeted_amount = Column(Float, nullable=False)
    target_revenue = Column(Float, nullable=False, default=0.0)

    __table_args__ = (
        Index("idx_budgets_year_quarter", "year", "quarter"),
    )


class FinancialTransaction(Base):
    __tablename__ = "financial_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_date = Column(Date, nullable=False, index=True)
    transaction_type = Column(String(20), nullable=False, index=True) # Inflow, Outflow
    category = Column(String(60), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    reference_id = Column(String(100), nullable=True)
    notes = Column(String(255), nullable=True)
