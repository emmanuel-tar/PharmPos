#!/usr/bin/env python3
"""
Product import/export CLI tool
Allows command-line import/export of products in CSV and JSON formats.

Usage:
  python product_tool.py export-csv <output_file> [--all]
  python product_tool.py export-json <output_file> [--all]
  python product_tool.py import-csv <input_file> [--update]
  python product_tool.py import-json <input_file> [--update]
  python product_tool.py template-csv <output_file>
  python product_tool.py template-json <output_file>
  python product_tool.py validate <input_file> [--format=csv|json]

Examples:
  python product_tool.py export-csv products_backup.csv
  python product_tool.py import-csv new_products.csv --update
  python product_tool.py template-csv template.csv
  python product_tool.py validate products.csv --format=csv
"""

import sys
import argparse
from pathlib import Path

from desktop_app.database import init_db
from desktop_app.product_manager import ProductImportExporter


def main():
    parser = argparse.ArgumentParser(
        description="Product Catalog Import/Export Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Export CSV
    export_csv = subparsers.add_parser("export-csv", help="Export products to CSV")
    export_csv.add_argument("output_file", help="Output CSV file path")
    export_csv.add_argument("--all", action="store_true", help="Export all products (including inactive)")

    # Export JSON
    export_json = subparsers.add_parser("export-json", help="Export products to JSON")
    export_json.add_argument("output_file", help="Output JSON file path")
    export_json.add_argument("--all", action="store_true", help="Export all products (including inactive)")

    # Import CSV
    import_csv = subparsers.add_parser("import-csv", help="Import products from CSV")
    import_csv.add_argument("input_file", help="Input CSV file path")
    import_csv.add_argument("--update", action="store_true", help="Update existing products if SKU matches")

    # Import JSON
    import_json = subparsers.add_parser("import-json", help="Import products from JSON")
    import_json.add_argument("input_file", help="Input JSON file path")
    import_json.add_argument("--update", action="store_true", help="Update existing products if SKU matches")

    # Template CSV
    template_csv = subparsers.add_parser("template-csv", help="Generate CSV template")
    template_csv.add_argument("output_file", help="Output template file path")

    # Template JSON
    template_json = subparsers.add_parser("template-json", help="Generate JSON template")
    template_json.add_argument("output_file", help="Output template file path")

    # Validate
    validate = subparsers.add_parser("validate", help="Validate import file")
    validate.add_argument("input_file", help="Input file path")
    validate.add_argument("--format", choices=["csv", "json"], default="csv", help="File format")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize database
    init_db()

    exporter = ProductImportExporter()

    try:
        if args.command == "export-csv":
            active_only = not args.all
            success, message = exporter.export_to_csv(args.output_file, active_only)
            print(message)
            sys.exit(0 if success else 1)

        elif args.command == "export-json":
            active_only = not args.all
            success, message = exporter.export_to_json(args.output_file, active_only)
            print(message)
            sys.exit(0 if success else 1)

        elif args.command == "import-csv":
            if not Path(args.input_file).exists():
                print(f"Error: File not found: {args.input_file}")
                sys.exit(1)
            
            count, errors = exporter.import_from_csv(args.input_file, args.update)
            print(f"Imported: {count} products")
            if errors:
                print(f"Errors: {len(errors)}")
                for error in errors[:10]:
                    print(f"  - {error}")
                if len(errors) > 10:
                    print(f"  ... and {len(errors) - 10} more errors")
            sys.exit(0 if not errors else 1)

        elif args.command == "import-json":
            if not Path(args.input_file).exists():
                print(f"Error: File not found: {args.input_file}")
                sys.exit(1)
            
            count, errors = exporter.import_from_json(args.input_file, args.update)
            print(f"Imported: {count} products")
            if errors:
                print(f"Errors: {len(errors)}")
                for error in errors[:10]:
                    print(f"  - {error}")
                if len(errors) > 10:
                    print(f"  ... and {len(errors) - 10} more errors")
            sys.exit(0 if not errors else 1)

        elif args.command == "template-csv":
            success, message = exporter.get_import_template(args.output_file, "csv")
            print(message)
            sys.exit(0 if success else 1)

        elif args.command == "template-json":
            success, message = exporter.get_import_template(args.output_file, "json")
            print(message)
            sys.exit(0 if success else 1)

        elif args.command == "validate":
            is_valid, errors = exporter.validate_file(args.input_file, args.format)
            if is_valid:
                print(f"✓ File is valid")
                sys.exit(0)
            else:
                print(f"✗ File validation failed: {len(errors)} errors")
                for error in errors[:10]:
                    print(f"  - {error}")
                if len(errors) > 10:
                    print(f"  ... and {len(errors) - 10} more errors")
                sys.exit(1)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
