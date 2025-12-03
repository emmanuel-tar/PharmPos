#!/usr/bin/env python3
"""
Test script for product import/export functionality
"""

from pathlib import Path
from decimal import Decimal
import tempfile
import os

from desktop_app.models import ProductService, get_session
from desktop_app.product_manager import ProductImportExporter
from desktop_app.database import init_db, dispose_engine
from datetime import datetime

# Use unique test DB name per run
TEST_DB = f"pharmapos_test_products_{datetime.now().strftime('%H%M%S%f')}.db"


def test_product_creation():
    """Test creating products."""
    print("=" * 60)
    print("TEST: Create Products")
    print("=" * 60)

    db_path = "pharmapos_test_products.db"
    init_db(db_path)

    session = get_session(db_path)
    service = ProductService(session)

    # Create test products
    products_data = [
        {
            "name": "Paracetamol 500mg",
            "sku": "PAR-500",
            "cost_price": Decimal("50"),
            "selling_price": Decimal("100"),
            "nafdac_number": "NAFDAC/001",
            "generic_name": "Acetaminophen",
            "barcode": "1111111111",
        },
        {
            "name": "Amoxicillin 250mg",
            "sku": "AMX-250",
            "cost_price": Decimal("150"),
            "selling_price": Decimal("300"),
            "nafdac_number": "NAFDAC/002",
            "generic_name": "Amoxicillin",
            "barcode": "2222222222",
        },
        {
            "name": "Ibuprofen 400mg",
            "sku": "IBU-400",
            "cost_price": Decimal("75"),
            "selling_price": Decimal("150"),
            "nafdac_number": "NAFDAC/003",
            "generic_name": "Ibuprofen",
            "barcode": "3333333333",
        },
    ]

    for product_data in products_data:
        # Skip if product with same SKU already exists (idempotent test)
        existing = service.get_product_by_sku(product_data["sku"])
        if existing:
            print(f"- Skipping existing product: {product_data['name']} ({product_data['sku']})")
            continue

        product = service.create_product(**product_data)
        print(f"✓ Created: {product['name']} (SKU: {product['sku']})")

    session.close()
    print()


def test_export_csv(db_path: str):
    """Test CSV export."""
    print("=" * 60)
    print("TEST: Export to CSV")
    print("=" * 60)

    export_file = "test_export.csv"
    exporter = ProductImportExporter(db_path)

    success, message = exporter.export_to_csv(export_file, active_only=False)
    print(message)

    if success and Path(export_file).exists():
        print(f"✓ CSV file created: {export_file}")
        with open(export_file, "r") as f:
            lines = f.readlines()
            print(f"  Lines: {len(lines)} (header + {len(lines) - 1} products)")
    else:
        print("✗ Export failed")

    # close session to release DB file locks
    try:
        exporter.close()
    except Exception:
        pass

    print()
    return export_file


def test_export_json(db_path: str):
    """Test JSON export."""
    print("=" * 60)
    print("TEST: Export to JSON")
    print("=" * 60)

    export_file = "test_export.json"
    exporter = ProductImportExporter(db_path)

    success, message = exporter.export_to_json(export_file, active_only=False)
    print(message)

    if success and Path(export_file).exists():
        print(f"✓ JSON file created: {export_file}")
        import json
        with open(export_file, "r") as f:
            products = json.load(f)
            print(f"  Products: {len(products)}")
    else:
        print("✗ Export failed")

    # close session to release DB file locks
    try:
        exporter.close()
    except Exception:
        pass

    print()
    return export_file


def test_import_csv():
    """Test CSV import."""
    print("=" * 60)
    print("TEST: Import from CSV")
    print("=" * 60)

    # Create test CSV file
    test_csv = "test_import.csv"
    csv_content = """name,generic_name,sku,barcode,nafdac_number,cost_price,selling_price,description
Metformin 500mg,Metformin,MET-500,9876543210,NAFDAC/010,200,400,Diabetes medication
Lisinopril 10mg,Lisinopril,LIS-10,9876543211,NAFDAC/011,150,300,Blood pressure medication
Atorvastatin 20mg,Atorvastatin,ATO-20,9876543212,NAFDAC/012,300,600,Cholesterol medication
"""

    with open(test_csv, "w") as f:
        f.write(csv_content)

    init_db(TEST_DB)
    exporter = ProductImportExporter(TEST_DB)

    # Validate first
    is_valid, errors = exporter.validate_file(test_csv, "csv")
    if is_valid:
        print(f"✓ File validation passed")
    else:
        print(f"✗ File validation failed:")
        for error in errors:
            print(f"  - {error}")
        return

    # Import
    count, errors = exporter.import_from_csv(test_csv, update_existing=False)
    print(f"✓ Imported {count} products")

    # close importer session
    try:
        exporter.close()
    except Exception:
        pass

    if errors:
        print(f"⚠ {len(errors)} errors/warnings:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✓ No errors")

    # Verify
    session = get_session(TEST_DB)
    service = ProductService(session)
    all_products = service.get_all_products(active_only=False)
    print(f"✓ Total products in DB: {len(all_products)}")
    session.close()

    print()


def test_import_json():
    """Test JSON import."""
    print("=" * 60)
    print("TEST: Import from JSON")
    print("=" * 60)

    # Create test JSON file
    test_json = "test_import.json"
    json_content = """[
  {
    "name": "Aspirin 100mg",
    "generic_name": "Acetylsalicylic Acid",
    "sku": "ASP-100",
    "barcode": "8765432100",
    "nafdac_number": "NAFDAC/020",
    "cost_price": 30,
    "selling_price": 60,
    "description": "Pain reliever"
  },
  {
    "name": "Omeprazole 20mg",
    "generic_name": "Omeprazole",
    "sku": "OMP-20",
    "barcode": "8765432101",
    "nafdac_number": "NAFDAC/021",
    "cost_price": 100,
    "selling_price": 200,
    "description": "Acid reflux medication"
  }
]
"""

    with open(test_json, "w") as f:
        f.write(json_content)

    db_path = "pharmapos_test_products.db"
    exporter = ProductImportExporter(db_path)

    # Validate first
    is_valid, errors = exporter.validate_file(test_json, "json")
    if is_valid:
        print(f"✓ File validation passed")
    else:
        print(f"✗ File validation failed:")
        for error in errors:
            print(f"  - {error}")
        return

    # Import
    count, errors = exporter.import_from_json(test_json, update_existing=False)
    print(f"✓ Imported {count} products")

    # close importer session
    try:
        exporter.close()
    except Exception:
        pass

    if errors:
        print(f"⚠ {len(errors)} errors/warnings:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✓ No errors")

    # Verify
    session = get_session(db_path)
    service = ProductService(session)
    all_products = service.get_all_products(active_only=False)
    print(f"✓ Total products in DB: {len(all_products)}")
    session.close()

    print()


def test_template_generation(db_path: str):
    """Test template generation."""
    print("=" * 60)
    print("TEST: Generate Import Templates")
    print("=" * 60)

    exporter = ProductImportExporter(db_path)

    # CSV template
    csv_template = "template_sample.csv"
    success, message = exporter.get_import_template(csv_template, "csv")
    print(f"CSV: {message}")

    # JSON template
    json_template = "template_sample.json"
    success, message = exporter.get_import_template(json_template, "json")
    print(f"JSON: {message}")

    # close session
    try:
        exporter.close()
    except Exception:
        pass

    print()


def test_update_existing(db_path: str):
    """Test updating existing products."""
    print("=" * 60)
    print("TEST: Update Existing Products")
    print("=" * 60)

    # Get current product
    session = get_session(db_path)
    service = ProductService(session)
    products = service.get_all_products(active_only=False)
    original = products[0]
    print(f"Original product: {original['name']} (SKU: {original['sku']}, Price: ₦{original['selling_price']})")
    session.close()

    # Create update CSV
    update_csv = "test_update.csv"
    csv_content = f"""name,generic_name,sku,barcode,nafdac_number,cost_price,selling_price,description
{original['name']} - Updated,{original.get('generic_name', '')},{original['sku']},barcode123,{original.get('nafdac_number', '')},150,500,Updated description
"""

    with open(update_csv, "w") as f:
        f.write(csv_content)

    exporter = ProductImportExporter(db_path)
    count, errors = exporter.import_from_csv(update_csv, update_existing=True)
    print(f"✓ Updated {count} products")

    # Verify update
    session = get_session(db_path)
    service = ProductService(session)
    updated = service.get_product(original["id"])
    print(f"Updated product: {updated['name']} (Price: ₦{updated['selling_price']})")
    session.close()
    try:
        exporter.close()
    except Exception:
        pass

    print()


def cleanup(files_to_remove: list):
    """Cleanup test files."""
    print("=" * 60)
    print("Cleanup")
    print("=" * 60)

    for filepath in files_to_remove:
        if Path(filepath).exists():
            try:
                os.remove(filepath)
                print(f"✓ Removed: {filepath}")
            except Exception as e:
                print(f"✗ Failed to remove {filepath}: {e}")

    print()


def main():
    """Run all tests."""
    print("\n")
    print("+" + "=" * 58 + "+")
    print("|  PRODUCT IMPORT/EXPORT TEST SUITE                         |")
    print("+" + "=" * 58 + "+")
    print("\n")

    db_path = "pharmapos_test_products.db"

    try:
        # Run tests
        test_product_creation()
        csv_file = test_export_csv(db_path)
        json_file = test_export_json(db_path)
        test_template_generation(db_path)
        test_import_csv()
        test_import_json()
        test_update_existing(db_path)

        # Summary
        print("=" * 60)
        print("✓ ALL TESTS COMPLETED")
        print("=" * 60)
        print()

        # Cleanup
        files = [
            csv_file,
            json_file,
            "test_import.csv",
            "test_import.json",
            "test_update.csv",
            "template_sample.csv",
            "template_sample.json",
        ]
        cleanup(files)

        # Dispose DB engine(s) to release file locks (Windows)
        try:
            dispose_engine(db_path)
        except Exception:
            pass
        try:
            dispose_engine(TEST_DB)
        except Exception:
            pass
        # Attempt to remove test DB file as part of cleanup
        if Path(db_path).exists():
            try:
                os.remove(db_path)
                print(f"✓ Removed: {db_path}")
            except Exception as e:
                print(f"- Could not remove {db_path}: {e}")

    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
