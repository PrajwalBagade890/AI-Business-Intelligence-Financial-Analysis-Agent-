"""Synthetic business data generator and database seeder."""

import random
from datetime import date, datetime, timedelta
import logging
from sqlalchemy.orm import Session
from app.database.connection import SessionLocal, init_db, engine
from app.database.models import Customer, Product, Sale, Expense, Budget, FinancialTransaction, Base

logger = logging.getLogger(__name__)

# Seed deterministic random for reproducibility
random.seed(42)

INDUSTRIES = ["Technology", "Healthcare", "Financial Services", "Retail & E-commerce", "Manufacturing", "Logistics"]
REGIONS = ["North America", "EMEA", "APAC", "LATAM"]
TIERS = ["Enterprise", "Mid-Market", "SMB"]

PRODUCT_DEFS = [
    {
        "product_name": "Enterprise Cloud BI Platform",
        "category": "SaaS Subscription",
        "unit_price": 24000.0,
        "unit_cost": 3600.0,
        "target_margin_pct": 85.0,
    },
    {
        "product_name": "BI Professional Edition",
        "category": "SaaS Subscription",
        "unit_price": 8000.0,
        "unit_cost": 1200.0,
        "target_margin_pct": 85.0,
    },
    {
        "product_name": "Edge Analytics Hardware Gateway",
        "category": "Hardware",
        "unit_price": 4500.0,
        "unit_cost": 2475.0,
        "target_margin_pct": 45.0,
    },
    {
        "product_name": "Professional Services & Implementation",
        "category": "Professional Services",
        "unit_price": 15000.0,
        "unit_cost": 9000.0,
        "target_margin_pct": 40.0,
    },
    {
        "product_name": "Security & Compliance Add-on",
        "category": "Security SaaS",
        "unit_price": 6000.0,
        "unit_cost": 600.0,
        "target_margin_pct": 90.0,
    },
    {
        "product_name": "AI Copilot Custom Fine-Tuning",
        "category": "AI Services",
        "unit_price": 12000.0,
        "unit_cost": 3600.0,
        "target_margin_pct": 70.0,
    },
]

EXPENSE_CATEGORIES = {
    "Research & Development": {
        "dept": "Engineering",
        "vendors": ["AWS Cloud Labs", "GitHub Enterprise", "OpenAI API", "Hugging Face Pro", "JetBrains"],
        "base_monthly": 45000.0,
    },
    "Sales & Marketing": {
        "dept": "Marketing",
        "vendors": ["Google Ads", "LinkedIn Marketing", "HubSpot", "Gartner Research", "SaaStr Annual Expo"],
        "base_monthly": 35000.0,
    },
    "General & Administrative": {
        "dept": "Operations",
        "vendors": ["WeWork Real Estate", "KPMG Audit & Tax", "Deloitte Advisory", "Stripe Fees", "Marsh McLennan Insurance"],
        "base_monthly": 20000.0,
    },
    "Cloud Infrastructure": {
        "dept": "IT Infrastructure",
        "vendors": ["Amazon Web Services", "Cloudflare CDN", "Snowflake Data Cloud", "Datadog Telemetry", "MongoDB Atlas"],
        "base_monthly": 28000.0,
    },
    "Customer Support & Success": {
        "dept": "Customer Success",
        "vendors": ["Zendesk Suite", "Intercom Messenger", "Skilljar Academy", "Gainsight CS"],
        "base_monthly": 15000.0,
    },
}

CUSTOMER_PREFIXES = [
    "Apex", "Vertex", "Quantum", "Nexus", "Pinnacle", "Starlight", "Horizon", "Catalyst", "Aegis", "Vanguard",
    "Silverline", "Omni", "Pulse", "Stratosphere", "Bluefin", "Titan", "Helix", "Synergy", "Beacon", "Solstice"
]
CUSTOMER_SUFFIXES = [
    "Logistics", "Health", "Capital", "Technologies", "Retail Group", "Energy", "Networks", "Solutions",
    "Systems", "Holdings", "Labs", "Dynamics", "Enterprises", "Financial", "Automotive"
]


def generate_company_name():
    return f"{random.choice(CUSTOMER_PREFIXES)} {random.choice(CUSTOMER_SUFFIXES)}"


def seed_database(db: Session = None, force_recreate: bool = False) -> dict:
    """Populate database with complete synthetic business dataset."""
    close_session_at_end = False
    if db is None:
        if force_recreate:
            Base.metadata.drop_all(bind=engine)
        init_db()
        db = SessionLocal()
        close_session_at_end = True

    try:
        # Check if already seeded
        existing_customers = db.query(Customer).count()
        if existing_customers > 0 and not force_recreate:
            logger.info(f"Database already populated with {existing_customers} customers. Skipping seed.")
            return {"status": "already_seeded", "customers": existing_customers}

        logger.info("Starting database seeding...")

        # 1. Insert Products
        products = []
        for pdef in PRODUCT_DEFS:
            prod = Product(**pdef)
            db.add(prod)
            products.append(prod)
        db.flush()

        # 2. Insert Customers (120 accounts)
        customers = []
        start_date = date(2023, 6, 1)
        used_names = set()

        for _ in range(120):
            while True:
                cname = generate_company_name()
                if cname not in used_names:
                    used_names.add(cname)
                    break

            days_offset = random.randint(0, 700)
            signup = start_date + timedelta(days=days_offset)
            cust = Customer(
                customer_name=cname,
                industry=random.choice(INDUSTRIES),
                region=random.choice(REGIONS),
                tier=random.choices(TIERS, weights=[0.25, 0.45, 0.30])[0],
                signup_date=signup,
                is_active=random.random() > 0.06,  # 6% churn
            )
            db.add(cust)
            customers.append(cust)
        db.flush()

        # 3. Generate Sales across 2024, 2025, and Q1 2026
        # Simulating seasonal growth and quarterly distribution
        sales_records = []
        order_counter = 1001
        current_date = date(2024, 1, 2)
        end_date = date(2026, 3, 31)

        while current_date <= end_date:
            year = current_date.year
            month = current_date.month

            # Growth multiplier: 2024 = 1.0, 2025 = 1.28, 2026 = 1.45
            growth_mult = 1.0 if year == 2024 else (1.28 if year == 2025 else 1.45)
            # Seasonality: Q4 (Oct-Dec) is strongest (+35%), Q3 (Jul-Sep) slight dip (-10%)
            seasonal_mult = 1.35 if month in [10, 11, 12] else (0.90 if month in [7, 8] else 1.05)

            # Daily order volume: 3 to 7 orders per day
            daily_order_count = int(random.randint(3, 7) * growth_mult * seasonal_mult * 0.8)
            active_customers_pool = [c for c in customers if c.signup_date <= current_date]

            if active_customers_pool:
                for _ in range(daily_order_count):
                    cust = random.choice(active_customers_pool)
                    prod = random.choice(products)

                    # Quantity depends on product type
                    if prod.category == "SaaS Subscription":
                        qty = random.choices([1, 2, 5, 10], weights=[0.60, 0.25, 0.10, 0.05])[0]
                    elif prod.category == "Hardware":
                        qty = random.randint(1, 8)
                    else:
                        qty = 1

                    # Tier discounts
                    discount_pct = 0.0
                    if cust.tier == "Enterprise":
                        discount_pct = random.choice([0.05, 0.10, 0.15])
                    elif cust.tier == "Mid-Market":
                        discount_pct = random.choice([0.0, 0.05])

                    gross_amt = round(prod.unit_price * qty, 2)
                    net_amt = round(gross_amt * (1.0 - discount_pct), 2)
                    cogs_amt = round(prod.unit_cost * qty, 2)
                    gross_prof = round(net_amt - cogs_amt, 2)

                    status = random.choices(["Completed", "Pending", "Refunded"], weights=[0.95, 0.03, 0.02])[0]
                    if status == "Refunded":
                        gross_prof = 0.0

                    sale = Sale(
                        order_number=f"ORD-{year}-{order_counter:06d}",
                        customer_id=cust.id,
                        product_id=prod.id,
                        order_date=current_date,
                        quantity=qty,
                        unit_price=prod.unit_price,
                        discount_pct=discount_pct,
                        gross_amount=gross_amt,
                        net_amount=net_amt,
                        cogs_amount=cogs_amt,
                        gross_profit=gross_prof,
                        payment_status=status,
                        region=cust.region,
                    )
                    db.add(sale)
                    order_counter += 1

            current_date += timedelta(days=1)

        db.flush()

        # 4. Generate Monthly Expenses
        current_month = date(2024, 1, 1)
        while current_month <= end_date:
            year = current_month.year
            month = current_month.month
            growth_mult = 1.0 if year == 2024 else (1.20 if year == 2025 else 1.35)

            for cat_name, cat_info in EXPENSE_CATEGORIES.items():
                # Base expense with random variance (+/- 10%)
                base_amt = cat_info["base_monthly"] * growth_mult
                variance = random.uniform(0.92, 1.08)
                amt = base_amt * variance

                # Anomaly 1: Cloud Infrastructure spike in Nov 2025 (+65% unoptimized AI workload)
                if cat_name == "Cloud Infrastructure" and year == 2025 and month == 11:
                    amt *= 1.65

                # Anomaly 2: Sales & Marketing conference spike in March 2025 (+50%)
                if cat_name == "Sales & Marketing" and year == 2025 and month == 3:
                    amt *= 1.50

                exp = Expense(
                    expense_date=current_month.replace(day=random.randint(15, 25)),
                    category=cat_name,
                    department=cat_info["dept"],
                    vendor=random.choice(cat_info["vendors"]),
                    description=f"Monthly recurring & operational spend for {cat_name}",
                    amount=round(amt, 2),
                    payment_status="Paid",
                )
                db.add(exp)

            # Move to next month
            if month == 12:
                current_month = date(year + 1, 1, 1)
            else:
                current_month = date(year, month + 1, 1)

        db.flush()

        # 5. Generate Budgets (2024, 2025, 2026)
        for yr in [2024, 2025, 2026]:
            for m in range(1, 13 if yr < 2026 else 4):
                q = f"Q{(m-1)//3 + 1}"
                # Target revenue per month
                monthly_target_rev = 350000.0 * (1.0 if yr == 2024 else (1.25 if yr == 2025 else 1.45))
                if m in [10, 11, 12]:
                    monthly_target_rev *= 1.30

                for cat_name, cat_info in EXPENSE_CATEGORIES.items():
                    budgeted_exp = cat_info["base_monthly"] * (1.0 if yr == 2024 else (1.18 if yr == 2025 else 1.30))
                    b = Budget(
                        year=yr,
                        quarter=q,
                        month=m,
                        category=cat_name,
                        department=cat_info["dept"],
                        budgeted_amount=round(budgeted_exp, 2),
                        target_revenue=round(monthly_target_rev, 2),
                    )
                    db.add(b)

        db.flush()

        # 6. Generate Cashflow / Financial Transactions
        tx_counter = 5001
        # Sample cash inflows from key enterprise payments & outflows
        for yr in [2024, 2025, 2026]:
            for m in range(1, 13 if yr < 2026 else 4):
                # Monthly payroll outflow
                db.add(FinancialTransaction(
                    transaction_date=date(yr, m, 28),
                    transaction_type="Outflow",
                    category="Payroll",
                    amount=round(120000.0 * (1.0 if yr == 2024 else 1.22), 2),
                    reference_id=f"TX-{yr}-{tx_counter}",
                    notes="Monthly all-hands payroll execution",
                ))
                tx_counter += 1

                # Monthly cloud hosting outflow
                db.add(FinancialTransaction(
                    transaction_date=date(yr, m, 5),
                    transaction_type="Outflow",
                    category="Cloud Hosting",
                    amount=round(28000.0 * (1.0 if yr == 2024 else 1.25), 2),
                    reference_id=f"TX-{yr}-{tx_counter}",
                    notes="Primary AWS consolidated billing",
                ))
                tx_counter += 1

        db.commit()

        counts = {
            "status": "success",
            "customers": db.query(Customer).count(),
            "products": db.query(Product).count(),
            "sales": db.query(Sale).count(),
            "expenses": db.query(Expense).count(),
            "budgets": db.query(Budget).count(),
            "transactions": db.query(FinancialTransaction).count(),
        }
        logger.info(f"Database seeded successfully: {counts}")
        return counts

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed database: {e}")
        raise
    finally:
        if close_session_at_end:
            db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = seed_database(force_recreate=True)
    print("Seed result:", result)
