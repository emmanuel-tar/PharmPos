"""
Product Manager - Import/Export and Bulk Operations

Handles product catalog management including CSV import/export,
bulk operations, and data validation.
"""

import csv
import json
from decimal import Decimal
from typing import List, Tuple, Optional, Dict
from datetime import datetime
import os

from desktop_app.models import ProductService, get_session


class ProductImportExporter:
    """Handle product import/export operations."""

    def __init__(self, db_path: Optional[str] = None):
        self.session = get_session(db_path)
        self.product_service = ProductService(self.session)

    def close(self) -> None:
        """Close the underlying DB session."""
        try:
            if self.session:
                self.session.close()
        except Exception:
            pass

    def export_to_csv(self, filepath: str, active_only: bool = True) -> Tuple[bool, str]:
        """
        Export products to CSV file.

        Args:
            filepath: Output CSV file path
            active_only: Export only active products if True

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            products = self.product_service.get_all_products(active_only=active_only)

            if not products:
                return False, "No products to export"

            # Define CSV columns
            fieldnames = [
                "id",
                "name",
                "generic_name",
                "sku",
                "barcode",
                "nafdac_number",
                "cost_price",
                "selling_price",
                "description",
                "is_active",
            ]

            with open(filepath, "w", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for product in products:
                    writer.writerow({field: product.get(field, "") for field in fieldnames})

            return True, f"Exported {len(products)} products to {filepath}"

        except Exception as e:
            return False, f"Export failed: {str(e)}"

    def export_to_json(self, filepath: str, active_only: bool = True) -> Tuple[bool, str]:
        """
        Export products to JSON file.

        Args:
            filepath: Output JSON file path
            active_only: Export only active products if True

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            products = self.product_service.get_all_products(active_only=active_only)

            if not products:
                return False, "No products to export"

            # Convert Decimal objects to float for JSON serialization
            products_json = []
            for product in products:
                product_dict = dict(product)
                if isinstance(product_dict.get("cost_price"), Decimal):
                    product_dict["cost_price"] = float(product_dict["cost_price"])
                if isinstance(product_dict.get("selling_price"), Decimal):
                    product_dict["selling_price"] = float(product_dict["selling_price"])
                products_json.append(product_dict)

            with open(filepath, "w") as jsonfile:
                json.dump(products_json, jsonfile, indent=2, default=str)

            return True, f"Exported {len(products)} products to {filepath}"

        except Exception as e:
            return False, f"Export failed: {str(e)}"

    def import_from_csv(
        self, filepath: str, update_existing: bool = False
    ) -> Tuple[int, List[str]]:
        """
        Import products from CSV file.

        CSV should have columns: name, generic_name, sku, barcode, nafdac_number,
        cost_price, selling_price, description

        Args:
            filepath: Input CSV file path
            update_existing: Update existing products if SKU matches

        Returns:
            tuple: (count_imported: int, errors: List[str])
        """
        errors = []
        created_count = 0

        try:
            with open(filepath, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)

                for row_num, row in enumerate(reader, start=2):  # Start at 2 (row 1 is header)
                    try:
                        # Validate required fields
                        name = row.get("name", "").strip()
                        sku = row.get("sku", "").strip()
                        nafdac = row.get("nafdac_number", "").strip()
                        cost_price = row.get("cost_price", "0").strip()
                        selling_price = row.get("selling_price", "0").strip()

                        if not all([name, sku, nafdac, cost_price, selling_price]):
                            errors.append(
                                f"Row {row_num}: Missing required fields (name, sku, nafdac_number, cost_price, selling_price)"
                            )
                            continue

                        # Validate prices
                        try:
                            cost = Decimal(cost_price)
                            selling = Decimal(selling_price)
                            if cost < 0 or selling < 0:
                                raise ValueError("Prices cannot be negative")
                        except Exception as e:
                            errors.append(f"Row {row_num}: Invalid price format - {str(e)}")
                            continue

                        # Check if product exists
                        existing = self.product_service.get_product_by_sku(sku)

                        if existing:
                            if update_existing:
                                # Update existing product
                                self.product_service.update_product(
                                    existing["id"],
                                    name=name,
                                    generic_name=row.get("generic_name", ""),
                                    barcode=row.get("barcode", ""),
                                    cost_price=cost,
                                    selling_price=selling,
                                    description=row.get("description", ""),
                                )
                                created_count += 1
                            else:
                                errors.append(f"Row {row_num}: SKU '{sku}' already exists (skipped)")
                                continue
                        else:
                            # Create new product
                            self.product_service.create_product(
                                name=name,
                                sku=sku,
                                cost_price=cost,
                                selling_price=selling,
                                nafdac_number=nafdac,
                                generic_name=row.get("generic_name", ""),
                                barcode=row.get("barcode", ""),
                                description=row.get("description", ""),
                            )
                            created_count += 1

                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")

        except FileNotFoundError:
            errors.append(f"File not found: {filepath}")
        except Exception as e:
            errors.append(f"Import failed: {str(e)}")

        return created_count, errors

    def import_from_json(
        self, filepath: str, update_existing: bool = False
    ) -> Tuple[int, List[str]]:
        """
        Import products from JSON file.

        Args:
            filepath: Input JSON file path
            update_existing: Update existing products if SKU matches

        Returns:
            tuple: (count_imported: int, errors: List[str])
        """
        errors = []
        created_count = 0

        try:
            with open(filepath, "r", encoding="utf-8") as jsonfile:
                products_data = json.load(jsonfile)

                if not isinstance(products_data, list):
                    return 0, ["JSON must contain an array of products"]

                for idx, row in enumerate(products_data, start=1):
                    try:
                        # Validate required fields
                        name = row.get("name", "").strip() if row.get("name") else ""
                        sku = row.get("sku", "").strip() if row.get("sku") else ""
                        nafdac = row.get("nafdac_number", "").strip() if row.get("nafdac_number") else ""
                        cost_price = str(row.get("cost_price", "0")).strip()
                        selling_price = str(row.get("selling_price", "0")).strip()

                        if not all([name, sku, nafdac, cost_price, selling_price]):
                            errors.append(
                                f"Item {idx}: Missing required fields (name, sku, nafdac_number, cost_price, selling_price)"
                            )
                            continue

                        # Validate prices
                        try:
                            cost = Decimal(cost_price)
                            selling = Decimal(selling_price)
                            if cost < 0 or selling < 0:
                                raise ValueError("Prices cannot be negative")
                        except Exception as e:
                            errors.append(f"Item {idx}: Invalid price format - {str(e)}")
                            continue

                        # Check if product exists
                        existing = self.product_service.get_product_by_sku(sku)

                        if existing:
                            if update_existing:
                                # Update existing product
                                self.product_service.update_product(
                                    existing["id"],
                                    name=name,
                                    generic_name=row.get("generic_name", ""),
                                    barcode=row.get("barcode", ""),
                                    cost_price=cost,
                                    selling_price=selling,
                                    description=row.get("description", ""),
                                )
                                created_count += 1
                            else:
                                errors.append(f"Item {idx}: SKU '{sku}' already exists (skipped)")
                                continue
                        else:
                            # Create new product
                            self.product_service.create_product(
                                name=name,
                                sku=sku,
                                cost_price=cost,
                                selling_price=selling,
                                nafdac_number=nafdac,
                                generic_name=row.get("generic_name", ""),
                                barcode=row.get("barcode", ""),
                                description=row.get("description", ""),
                            )
                            created_count += 1

                    except Exception as e:
                        errors.append(f"Item {idx}: {str(e)}")

        except FileNotFoundError:
            errors.append(f"File not found: {filepath}")
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            errors.append(f"Import failed: {str(e)}")

        return created_count, errors

    def get_import_template(self, filepath: str, format: str = "csv") -> Tuple[bool, str]:
        """
        Generate an import template file.

        Args:
            filepath: Output file path
            format: 'csv' or 'json'

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            if format.lower() == "csv":
                with open(filepath, "w", newline="") as csvfile:
                    fieldnames = [
                        "name",
                        "generic_name",
                        "sku",
                        "barcode",
                        "nafdac_number",
                        "cost_price",
                        "selling_price",
                        "description",
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()

                    # Add sample row
                    sample = {
                        "name": "Paracetamol 500mg",
                        "generic_name": "Acetaminophen",
                        "sku": "PAR-500",
                        "barcode": "1234567890",
                        "nafdac_number": "NAFDAC/001",
                        "cost_price": "50.00",
                        "selling_price": "100.00",
                        "description": "Pain reliever and fever reducer",
                    }
                    writer.writerow(sample)

                return True, f"CSV template created: {filepath}"

            elif format.lower() == "json":
                template = [
                    {
                        "name": "Paracetamol 500mg",
                        "generic_name": "Acetaminophen",
                        "sku": "PAR-500",
                        "barcode": "1234567890",
                        "nafdac_number": "NAFDAC/001",
                        "cost_price": "50.00",
                        "selling_price": "100.00",
                        "description": "Pain reliever and fever reducer",
                    }
                ]

                with open(filepath, "w") as jsonfile:
                    json.dump(template, jsonfile, indent=2)

                return True, f"JSON template created: {filepath}"

            else:
                return False, "Format must be 'csv' or 'json'"

        except Exception as e:
            return False, f"Template creation failed: {str(e)}"

    def validate_file(self, filepath: str, format: str = "csv") -> Tuple[bool, List[str]]:
        """
        Validate import file without importing.

        Args:
            filepath: File path to validate
            format: 'csv' or 'json'

        Returns:
            tuple: (is_valid: bool, errors: List[str])
        """
        errors = []

        try:
            if format.lower() == "csv":
                with open(filepath, "r", encoding="utf-8") as csvfile:
                    reader = csv.DictReader(csvfile)

                    for row_num, row in enumerate(reader, start=2):
                        # Validate required fields
                        if not row.get("name", "").strip():
                            errors.append(f"Row {row_num}: Missing 'name'")
                        if not row.get("sku", "").strip():
                            errors.append(f"Row {row_num}: Missing 'sku'")
                        if not row.get("nafdac_number", "").strip():
                            errors.append(f"Row {row_num}: Missing 'nafdac_number'")

                        # Validate prices
                        try:
                            cost_price = row.get("cost_price", "0").strip()
                            selling_price = row.get("selling_price", "0").strip()
                            Decimal(cost_price)
                            Decimal(selling_price)
                        except Exception as e:
                            errors.append(f"Row {row_num}: Invalid price format - {str(e)}")

            elif format.lower() == "json":
                with open(filepath, "r", encoding="utf-8") as jsonfile:
                    products_data = json.load(jsonfile)

                    if not isinstance(products_data, list):
                        errors.append("JSON must contain an array of products")
                        return False, errors

                    for idx, row in enumerate(products_data, start=1):
                        if not row.get("name", "").strip():
                            errors.append(f"Item {idx}: Missing 'name'")
                        if not row.get("sku", "").strip():
                            errors.append(f"Item {idx}: Missing 'sku'")
                        if not row.get("nafdac_number", "").strip():
                            errors.append(f"Item {idx}: Missing 'nafdac_number'")

                        try:
                            cost_price = str(row.get("cost_price", "0")).strip()
                            selling_price = str(row.get("selling_price", "0")).strip()
                            Decimal(cost_price)
                            Decimal(selling_price)
                        except Exception as e:
                            errors.append(f"Item {idx}: Invalid price format - {str(e)}")

            else:
                errors.append("Format must be 'csv' or 'json'")

        except FileNotFoundError:
            errors.append(f"File not found: {filepath}")
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            errors.append(f"Validation failed: {str(e)}")

        return len(errors) == 0, errors


# Convenience functions
def export_products_csv(
    filepath: str, db_path: Optional[str] = None, active_only: bool = True
) -> Tuple[bool, str]:
    """Export products to CSV."""
    exporter = ProductImportExporter(db_path)
    return exporter.export_to_csv(filepath, active_only)


def export_products_json(
    filepath: str, db_path: Optional[str] = None, active_only: bool = True
) -> Tuple[bool, str]:
    """Export products to JSON."""
    exporter = ProductImportExporter(db_path)
    return exporter.export_to_json(filepath, active_only)


def import_products_csv(
    filepath: str, db_path: Optional[str] = None, update_existing: bool = False
) -> Tuple[int, List[str]]:
    """Import products from CSV."""
    importer = ProductImportExporter(db_path)
    return importer.import_from_csv(filepath, update_existing)


def import_products_json(
    filepath: str, db_path: Optional[str] = None, update_existing: bool = False
) -> Tuple[int, List[str]]:
    """Import products from JSON."""
    importer = ProductImportExporter(db_path)
    return importer.import_from_json(filepath, update_existing)
