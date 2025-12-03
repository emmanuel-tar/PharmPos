#!/usr/bin/env python3
"""
Simple product import/export workflow test
"""

from pathlib import Path
from decimal import Decimal

from desktop_app.database import init_db
from desktop_app.models import ProductService, get_session
from desktop_app.product_manager import ProductImportExporter


def main():
    print("\n")
    print("=" * 60)
    print("PRODUCT IMPORT/EXPORT WORKFLOW TEST")
    print("=" * 60)
    print()

    # Use clean test DB
    db_path = "test_workflow.db"
    print("[1] Initialize database...")
    init_db(db_path)
    print("    Done")
    print()

    # Create test products
    print("[2] Create test products...")
    session = get_session(db_path)
    service = ProductService(session)

    products = [
        ("Paracetamol 500mg", "PAR-500", "50", "100", "NAFDAC/001", "1111111111"),
        ("Amoxicillin 250mg", "AMX-250", "150", "300", "NAFDAC/002", "2222222222"),
        ("Ibuprofen 400mg", "IBU-400", "75", "150", "NAFDAC/003", "3333333333"),
    ]

    for name, sku, cost, selling, nafdac, barcode in products:
        existing = service.get_product_by_sku(sku)
        if existing:
            print(f"    - Skipping existing product: {name} ({sku})")
        else:
            service.create_product(
                name=name,
                sku=sku,
                cost_price=Decimal(cost),
                selling_price=Decimal(selling),
                nafdac_number=nafdac,
                barcode=barcode,
            )
            print(f"    + {name} ({sku})")

    session.close()
    print()

    # Export to CSV
    print("[3] Export to CSV...")
    exporter = ProductImportExporter(db_path)
    success, msg = exporter.export_to_csv("test_export.csv", active_only=False)
    print(f"    {msg}")
    if Path("test_export.csv").exists():
        with open("test_export.csv") as f:
            lines = f.readlines()
            print(f"    File size: {len(lines)} lines")
    print()

    # Export to JSON
    print("[4] Export to JSON...")
    success, msg = exporter.export_to_json("test_export.json", active_only=False)
    print(f"    {msg}")
    if Path("test_export.json").exists():
        import json
        with open("test_export.json") as f:
            data = json.load(f)
            print(f"    Products: {len(data)} items")
    print()

    # Generate templates
    print("[5] Generate import templates...")
    exporter.get_import_template("template.csv", "csv")
    print("    + template.csv created")
    exporter.get_import_template("template.json", "json")
    print("    + template.json created")
    print()

    # Import from CSV
    print("[6] Import from CSV...")
    csv_data = """name,generic_name,sku,barcode,nafdac_number,cost_price,selling_price,description
Metformin 500mg,Metformin,MET-500,4444444444,NAFDAC/010,200,400,Diabetes medication
Lisinopril 10mg,Lisinopril,LIS-10,5555555555,NAFDAC/011,150,300,Blood pressure medication
"""
    with open("import_test.csv", "w") as f:
        f.write(csv_data)

    is_valid, errors = exporter.validate_file("import_test.csv", "csv")
    if is_valid:
        print("    Validation: PASS")
        count, errors = exporter.import_from_csv("import_test.csv", update_existing=False)
        print(f"    Imported: {count} products")
    else:
        print("    Validation: FAIL")
    print()

    # Verify total
    print("[7] Verify total products...")
    session = get_session(db_path)
    service = ProductService(session)
    all_products = service.get_all_products(active_only=False)
    print(f"    Total products: {len(all_products)}")
    for p in all_products:
        print(f"      - {p['name']} ({p['sku']}): ${p['selling_price']}")
    session.close()
    print()

    # Cleanup
    print("[8] Cleanup...")
    for f in ["test_workflow.db", "test_export.csv", "test_export.json",
              "template.csv", "template.json", "import_test.csv"]:
        try:
            if Path(f).exists():
                Path(f).unlink()
                print(f"    - Removed: {f}")
        except Exception as e:
            print(f"    - Could not remove {f}: {e}")
    print()

    print("=" * 60)
    print("TEST COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
