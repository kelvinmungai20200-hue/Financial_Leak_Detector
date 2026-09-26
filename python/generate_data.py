import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker


# ============================================================
# FINANCIAL LEAK DETECTOR
# Synthetic Financial Data Generator
# ============================================================

fake = Faker()
random.seed(42)
np.random.seed(42)

# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2025, 12, 31)

NUM_EMPLOYEES = 300

# ------------------------------------------------------------
# DEPARTMENTS
# ------------------------------------------------------------

departments = [
    "Finance",
    "Human Resources",
    "Information Technology",
    "Sales",
    "Marketing",
    "Operations",
    "Customer Support",
    "Procurement",
    "Logistics",
    "Administration"
]

department_managers = {
    department: fake.name()
    for department in departments
}


# ============================================================
# 1. GENERATE DEPARTMENTS
# ============================================================

department_records = []

for department_id, department_name in enumerate(departments, start=1):
    department_records.append({
        "department_id": department_id,
        "department_name": department_name,
        "department_manager": department_managers[department_name]
    })

departments_df = pd.DataFrame(department_records)


# ============================================================
# 2. GENERATE EMPLOYEES
# ============================================================

job_titles = [
    "Accountant",
    "Analyst",
    "Developer",
    "Manager",
    "Sales Executive",
    "Marketing Officer",
    "HR Officer",
    "Customer Support Officer",
    "Procurement Officer",
    "Operations Officer",
    "Administrator",
    "Data Analyst",
    "Financial Analyst",
    "Project Manager"
]

employee_records = []

for employee_id in range(1, NUM_EMPLOYEES + 1):

    first_name = fake.first_name()
    last_name = fake.last_name()

    department_id = random.randint(1, len(departments))

    hire_date = fake.date_between(
        start_date="-6y",
        end_date="-30d"
    )

    employment_status = random.choices(
        ["ACTIVE", "INACTIVE", "ON_LEAVE"],
        weights=[88, 7, 5],
        k=1
    )[0]

    # Generate realistic salary ranges
    base_salary = round(
        random.uniform(35000, 250000),
        -2
    )

    employee_records.append({
        "employee_id": employee_id,
        "employee_code": f"EMP{employee_id:04d}",
        "first_name": first_name,
        "last_name": last_name,
        "department_id": department_id,
        "job_title": random.choice(job_titles),
        "employment_status": employment_status,
        "hire_date": hire_date,
        "base_salary": base_salary,
        "bank_account_last4": fake.numerify("####")
    })

employees_df = pd.DataFrame(employee_records)


# ============================================================
# 3. GENERATE PAYROLL
# ============================================================

payroll_records = []

months = pd.date_range(
    START_DATE,
    END_DATE,
    freq="MS"
)

payroll_id = 1

for _, employee in employees_df.iterrows():

    employee_id = employee["employee_id"]
    base_salary = float(employee["base_salary"])

    for month in months:

        # Most employees receive normal payroll
        overtime_hours = round(
            max(0, np.random.normal(8, 5)),
            2
        )

        overtime_rate = (base_salary / 160) * 1.5

        overtime_amount = round(
            overtime_hours * overtime_rate,
            2
        )

        # Bonuses occur occasionally
        if random.random() < 0.12:
            bonus_amount = round(
                random.uniform(5000, 40000),
                2
            )
        else:
            bonus_amount = 0

        allowance_amount = round(
            random.uniform(0, 15000),
            2
        )

        deductions = round(
            base_salary * random.uniform(0.05, 0.18),
            2
        )

        gross_salary = (
            base_salary
            + overtime_amount
            + bonus_amount
            + allowance_amount
        )

        net_salary = round(
            gross_salary - deductions,
            2
        )

        payment_date = month + timedelta(
            days=random.randint(25, 30)
        )

        payroll_records.append({
            "payroll_id": payroll_id,
            "employee_id": employee_id,
            "payroll_month": month.date(),
            "base_salary": base_salary,
            "overtime_hours": overtime_hours,
            "overtime_amount": overtime_amount,
            "bonus_amount": bonus_amount,
            "allowance_amount": allowance_amount,
            "deductions": deductions,
            "net_salary": net_salary,
            "payment_date": payment_date.date(),
            "payment_reference": f"PAY-{month.strftime('%Y%m')}-{employee_id:04d}"
        })

        payroll_id += 1


payroll_df = pd.DataFrame(payroll_records)


# ============================================================
# 4. PLANT PAYROLL ANOMALIES
# ============================================================

# ------------------------------------------------------------
# Anomaly A: Unusually high overtime
# ------------------------------------------------------------

overtime_indices = payroll_df.sample(
    n=25,
    random_state=42
).index

payroll_df.loc[overtime_indices, "overtime_hours"] = np.random.uniform(
    50,
    100,
    len(overtime_indices)
).round(2)

payroll_df.loc[overtime_indices, "overtime_amount"] = (
    payroll_df.loc[overtime_indices, "overtime_hours"]
    * (
        payroll_df.loc[overtime_indices, "base_salary"] / 160
    )
    * 1.5
).round(2)


# ------------------------------------------------------------
# Anomaly B: Unusually large bonuses
# ------------------------------------------------------------

bonus_indices = payroll_df.sample(
    n=15,
    random_state=99
).index

payroll_df.loc[bonus_indices, "bonus_amount"] = np.random.uniform(
    80000,
    200000,
    len(bonus_indices)
).round(2)


# ------------------------------------------------------------
# Recalculate net salary after anomalies
# ------------------------------------------------------------

payroll_df["gross_salary"] = (
    payroll_df["base_salary"]
    + payroll_df["overtime_amount"]
    + payroll_df["bonus_amount"]
    + payroll_df["allowance_amount"]
)

payroll_df["net_salary"] = (
    payroll_df["gross_salary"]
    - payroll_df["deductions"]
).round(2)

payroll_df.drop(
    columns=["gross_salary"],
    inplace=True
)


# ============================================================
# 5. DUPLICATE PAYMENTS
# ============================================================

duplicate_source = payroll_df.sample(
    n=20,
    random_state=123
).copy()

duplicate_source["payroll_id"] = range(
    payroll_df["payroll_id"].max() + 1,
    payroll_df["payroll_id"].max() + 1 + len(duplicate_source)
)

duplicate_source["payment_reference"] = (
    duplicate_source["payment_reference"] + "-DUP"
)

payroll_df = pd.concat(
    [payroll_df, duplicate_source],
    ignore_index=True
)


# ============================================================
# 6. FINANCIAL TRANSACTIONS
# ============================================================

transaction_categories = {
    "INCOME": [
        "Sales Revenue",
        "Service Revenue",
        "Consulting Revenue",
        "Subscription Revenue",
        "Other Income"
    ],
    "EXPENSE": [
        "Rent",
        "Utilities",
        "Marketing",
        "Office Supplies",
        "Travel",
        "Software",
        "Equipment",
        "Professional Services",
        "Insurance",
        "Payroll",
        "Logistics",
        "Maintenance"
    ]
}

payment_methods = [
    "Bank Transfer",
    "Credit Card",
    "Debit Card",
    "Mobile Money",
    "Cash"
]

transaction_records = []

num_transactions = 8000

for transaction_id in range(1, num_transactions + 1):

    transaction_date = fake.date_between(
        start_date=START_DATE,
        end_date=END_DATE
    )

    transaction_type = random.choices(
        ["INCOME", "EXPENSE"],
        weights=[35, 65],
        k=1
    )[0]

    category = random.choice(
        transaction_categories[transaction_type]
    )

    if transaction_type == "INCOME":
        amount = round(
            random.uniform(10000, 1000000),
            2
        )
    else:
        amount = round(
            random.uniform(1000, 500000),
            2
        )

    department_id = random.randint(
        1,
        len(departments)
    )

    employee_id = None

    # Some transactions are associated with employees
    if random.random() < 0.25:
        employee_id = random.randint(
            1,
            NUM_EMPLOYEES
        )

    transaction_records.append({
        "transaction_id": transaction_id,
        "transaction_date": transaction_date,
        "transaction_type": transaction_type,
        "category": category,
        "description": fake.sentence(nb_words=5),
        "amount": amount,
        "department_id": department_id,
        "employee_id": employee_id,
        "payment_method": random.choice(payment_methods),
        "transaction_reference": f"TXN-{transaction_id:07d}"
    })


transactions_df = pd.DataFrame(
    transaction_records
)


# ============================================================
# 7. PLANT SUSPICIOUS TRANSACTIONS
# ============================================================

suspicious_indices = transactions_df[
    transactions_df["transaction_type"] == "EXPENSE"
].sample(
    n=30,
    random_state=202
).index

transactions_df.loc[
    suspicious_indices,
    "amount"
] = np.random.uniform(
    700000,
    2000000,
    len(suspicious_indices)
).round(2)

transactions_df.loc[
    suspicious_indices,
    "description"
] = "Unusually large expense transaction"


# ============================================================
# 8. INACTIVE EMPLOYEE PAYMENTS
# ============================================================

inactive_employees = employees_df[
    employees_df["employment_status"] == "INACTIVE"
]["employee_id"].tolist()

if inactive_employees:

    inactive_indices = transactions_df.sample(
        n=min(20, len(transactions_df)),
        random_state=303
    ).index

    transactions_df.loc[
        inactive_indices,
        "employee_id"
    ] = random.choices(
        inactive_employees,
        k=len(inactive_indices)
    )

    transactions_df.loc[
        inactive_indices,
        "description"
    ] = "Payment linked to inactive employee"


# ============================================================
# 9. CASH FLOW
# ============================================================

cash_flow_records = []

for month in months:

    monthly_income = transactions_df[
        (transactions_df["transaction_type"] == "INCOME")
        & (
            pd.to_datetime(
                transactions_df["transaction_date"]
            ).dt.to_period("M")
            == month.to_period("M")
        )
    ]["amount"].sum()

    monthly_expenses = transactions_df[
        (transactions_df["transaction_type"] == "EXPENSE")
        & (
            pd.to_datetime(
                transactions_df["transaction_date"]
            ).dt.to_period("M")
            == month.to_period("M")
        )
    ]["amount"].sum()

    cash_flow_records.append({
        "flow_date": month.date(),
        "inflow": round(monthly_income, 2),
        "outflow": round(monthly_expenses, 2),
        "description": "Monthly consolidated cash flow",
        "source_category": "All Sources"
    })


cash_flow_df = pd.DataFrame(
    cash_flow_records
)


# ============================================================
# 10. SAVE DATASETS
# ============================================================

departments_df.to_csv(
    os.path.join(OUTPUT_DIR, "departments.csv"),
    index=False
)

employees_df.to_csv(
    os.path.join(OUTPUT_DIR, "employees.csv"),
    index=False
)

payroll_df.to_csv(
    os.path.join(OUTPUT_DIR, "payroll.csv"),
    index=False
)

transactions_df.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "financial_transactions.csv"
    ),
    index=False
)

cash_flow_df.to_csv(
    os.path.join(OUTPUT_DIR, "cash_flow.csv"),
    index=False
)


# ============================================================
# 11. SUMMARY
# ============================================================

print("\n==========================================")
print("FINANCIAL LEAK DETECTOR DATA GENERATED")
print("==========================================")

print(f"Departments:              {len(departments_df):,}")
print(f"Employees:                {len(employees_df):,}")
print(f"Payroll records:          {len(payroll_df):,}")
print(f"Financial transactions:   {len(transactions_df):,}")
print(f"Cash flow records:        {len(cash_flow_df):,}")

print("\nFiles saved to:")
print(OUTPUT_DIR)

print("\nGeneration completed successfully.")