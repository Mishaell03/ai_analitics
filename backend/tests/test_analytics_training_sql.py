"""Статические проверки SQL-файлов: без запуска миграций и подключения к БД."""

import ast
from datetime import date
from decimal import Decimal
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1] / "infra/postgres/analytics_training"


def seed_rows():
    source = (ROOT / "seeds/R__retail_sales.sql").read_text()
    tables = {}
    for match in re.finditer(
        r"INSERT INTO (\w+)\s*\((.*?)\)\s*VALUES\s*(.*?)\s*ON CONFLICT \((\w+)\) DO NOTHING;",
        source, re.DOTALL,
    ):
        table, columns, values, primary_key = match.groups()
        columns = [column.strip() for column in columns.split(",")]
        # Сиды содержат только литеральные VALUES. Это разбор текста Python,
        # не выполнение SQL и не проверка синтаксиса PostgreSQL сервером.
        rows = ast.literal_eval("[" + re.sub(r"\bNULL\b", "None", values) + "]")
        assert all(len(row) == len(columns) for row in rows)
        tables[table] = [dict(zip(columns, row)) for row in rows]
        assert len({row[primary_key] for row in tables[table]}) == len(rows)
    return tables


class AnalyticsTrainingSqlTests(unittest.TestCase):
    def test_migration_order_and_required_columns(self):
        expected = {
            "V1__customers.sql": ["customer_id VARCHAR(20) PRIMARY KEY", "city TEXT", "registration_date DATE"],
            "V2__products.sql": ["product TEXT PRIMARY KEY", "brand TEXT", "supplier TEXT"],
            "V3__orders.sql": ["order_id BIGINT PRIMARY KEY", "customer_id VARCHAR(20) NOT NULL", "sales_channel TEXT"],
            "V4__order_items.sql": [
                "line_item_id BIGINT PRIMARY KEY", "order_id BIGINT NOT NULL", "order_date DATE NOT NULL",
                "customer_id VARCHAR(20) NOT NULL", "product TEXT NOT NULL", "category TEXT NOT NULL",
                "quantity INTEGER NOT NULL", "unit_price NUMERIC(12,2) NOT NULL", "status VARCHAR(20) NOT NULL",
            ],
        }
        self.assertEqual(sorted(path.name for path in (ROOT / "migrations").glob("*.sql")), sorted(expected))
        for name, columns in expected.items():
            source = (ROOT / "migrations" / name).read_text()
            for column in columns:
                self.assertIn(column, source)

    def test_foreign_keys_checks_and_indexes(self):
        orders = (ROOT / "migrations/V3__orders.sql").read_text()
        items = (ROOT / "migrations/V4__order_items.sql").read_text()
        self.assertIn("REFERENCES customers(customer_id)", orders)
        for reference in ["orders(order_id)", "customers(customer_id)", "products(product)"]:
            self.assertIn(f"REFERENCES {reference}", items)
        for check in ["quantity > 0", "unit_price >= 0", "status IN ('completed', 'cancelled')"]:
            self.assertIn(f"CHECK ({check})", items)
        indexes = re.findall(r"CREATE INDEX IF NOT EXISTS \w+ ON (\w+)\((\w+)\);", orders + items)
        self.assertEqual(set(indexes), {
            ("orders", "customer_id"), ("order_items", "order_id"), ("order_items", "customer_id"),
            ("order_items", "product"), ("order_items", "order_date"),
        })
        self.assertEqual(len(indexes), 5)

    def test_seed_counts_primary_keys_and_foreign_keys(self):
        rows = seed_rows()
        self.assertEqual({table: len(values) for table, values in rows.items()}, {
            "customers": 12, "products": 10, "orders": 20, "order_items": 36,
        })
        customers = {row["customer_id"] for row in rows["customers"]}
        products = {row["product"] for row in rows["products"]}
        orders = {row["order_id"]: row for row in rows["orders"]}
        for order in orders.values():
            self.assertIn(order["customer_id"], customers)
        for item in rows["order_items"]:
            self.assertIn(item["order_id"], orders)
            self.assertIn(item["customer_id"], customers)
            self.assertIn(item["product"], products)
            self.assertEqual(item["customer_id"], orders[item["order_id"]]["customer_id"])

    def test_item_values_dates_and_order_consistency(self):
        rows = seed_rows()
        registrations = {row["customer_id"]: row["registration_date"] for row in rows["customers"]}
        order_details = {}
        for item in rows["order_items"]:
            self.assertTrue(all(value is not None for value in item.values()))
            self.assertGreater(item["quantity"], 0)
            self.assertIsInstance(item["quantity"], int)
            self.assertGreaterEqual(Decimal(str(item["unit_price"])), 0)
            self.assertIn(item["status"], {"completed", "cancelled"})
            order_date = date.fromisoformat(item["order_date"])
            registration = registrations[item["customer_id"]]
            if registration:
                self.assertLessEqual(date.fromisoformat(registration), order_date)
            details = (item["order_date"], item["status"])
            self.assertEqual(order_details.setdefault(item["order_id"], details), details)

    def test_seed_supports_joins_nulls_and_sales_analysis(self):
        rows = seed_rows()
        self.assertEqual({item["status"] for item in rows["order_items"]}, {"completed", "cancelled"})
        self.assertEqual({order["sales_channel"] for order in rows["orders"]}, {
            "website", "mobile_app", "marketplace", "store", None,
        })
        self.assertTrue({row["customer_id"] for row in rows["customers"]}
                        - {row["customer_id"] for row in rows["orders"]})
        self.assertTrue({row["product"] for row in rows["products"]}
                        - {row["product"] for row in rows["order_items"]})
        self.assertLess(len({row["customer_id"] for row in rows["orders"]}), len(rows["orders"]))
        self.assertEqual(len({item["order_date"][:7] for item in rows["order_items"]}), 3)

    def test_scripts_do_not_delete_or_overwrite_existing_data(self):
        for path in ROOT.rglob("*.sql"):
            source = re.sub(r"--[^\n]*", "", path.read_text())
            self.assertNotRegex(source, r"(?i)\b(DROP|TRUNCATE|DELETE|UPDATE|ALTER|GRANT|REVOKE)\b")
        seed = (ROOT / "seeds/R__retail_sales.sql").read_text()
        self.assertEqual(seed.count("DO NOTHING;"), 4)


if __name__ == "__main__":
    unittest.main()
