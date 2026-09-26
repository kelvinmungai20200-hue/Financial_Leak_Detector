import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values


# ============================================================
# FINANCIAL LEAK DETECTOR
# CSV → PostgreSQL Loader
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "financial_leak_detector_db",
    "user": "postgres",
    "password": "2583K"
}


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )


# ============================================================
# LOAD CSV
# ============================================================

def load_csv(filename):

    filepath = os.path.join(
        DATA_DIR,
        filename
    )

    print(f"Loading {filename}...")

    return pd.read_csv(filepath)


# ============================================================
# CONVERT PANDAS VALUES TO PYTHON VALUES
# ============================================================

def clean_value(value):

    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        return value.item()

    return value


# ============================================================
# INSERT DATA
# ============================================================

def insert_data(
    connection,
    table_name,
    dataframe,
    columns
):

    cleaned_values = []

    for row in dataframe[columns].itertuples(
        index=False,
        name=None
    ):

        cleaned_row = tuple(
            clean_value(value)
            for value in row
        )

        cleaned_values.append(
            cleaned_row
        )

    query = f"""
        INSERT INTO {table_name}
        ({', '.join(columns)})
        VALUES %s
    """

    with connection.cursor() as cursor:

        execute_values(
            cursor,
            query,
            cleaned_values,
            page_size=1000
        )

    connection.commit()

    print(
        f"Inserted {len(cleaned_values):,} rows into {table_name}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n==========================================")
    print("FINANCIAL LEAK DETECTOR")
    print("Loading data into PostgreSQL")
    print("==========================================\n")

    connection = None

    try:

        connection = get_connection()

        print(
            "Connected to PostgreSQL successfully.\n"
        )


        # ====================================================
        # DEPARTMENTS
        # ====================================================

        departments = load_csv(
            "departments.csv"
        )

        insert_data(
            connection,
            "departments",
            departments,
            [
                "department_id",
                "department_name",
                "department_manager"
            ]
        )


        # ====================================================
        # EMPLOYEES
        # ====================================================

        employees = load_csv(
            "employees.csv"
        )

        insert_data(
            connection,
            "employees",
            employees,
            [
                "employee_id",
                "employee_code",
                "first_name",
                "last_name",
                "department_id",
                "job_title",
                "employment_status",
                "hire_date",
                "base_salary",
                "bank_account_last4"
            ]
        )


        # ====================================================
        # PAYROLL
        # ====================================================

        payroll = load_csv(
            "payroll.csv"
        )

        insert_data(
            connection,
            "payroll",
            payroll,
            [
                "payroll_id",
                "employee_id",
                "payroll_month",
                "base_salary",
                "overtime_hours",
                "overtime_amount",
                "bonus_amount",
                "allowance_amount",
                "deductions",
                "net_salary",
                "payment_date",
                "payment_reference"
            ]
        )


        # ====================================================
        # FINANCIAL TRANSACTIONS
        # ====================================================

        transactions = load_csv(
            "financial_transactions.csv"
        )

        insert_data(
            connection,
            "financial_transactions",
            transactions,
            [
                "transaction_id",
                "transaction_date",
                "transaction_type",
                "category",
                "description",
                "amount",
                "department_id",
                "employee_id",
                "payment_method",
                "transaction_reference"
            ]
        )


        # ====================================================
        # CASH FLOW
        # ====================================================

        cash_flow = load_csv(
            "cash_flow.csv"
        )

        insert_data(
            connection,
            "cash_flow",
            cash_flow,
            [
                "flow_date",
                "inflow",
                "outflow",
                "description",
                "source_category"
            ]
        )


        print("\n==========================================")
        print("DATA LOAD COMPLETED SUCCESSFULLY")
        print("==========================================")

    except Exception as error:

        print("\nERROR:")
        print(error)

        if connection:
            connection.rollback()

    finally:

        if connection:
            connection.close()

            print(
                "\nPostgreSQL connection closed."
            )


if __name__ == "__main__":
    main()