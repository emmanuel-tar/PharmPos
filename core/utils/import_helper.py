import csv
from typing import List, Dict, Optional
from decimal import Decimal

class ImportExportHelper:
    @staticmethod
    def export_to_csv(data: List[dict], file_path: str):
        """Export list of dictionaries to CSV."""
        if not data:
            return
        
        keys = data[0].keys()
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)

    @staticmethod
    def export_to_excel(data: List[dict], file_path: str):
        """Export list of dictionaries to Excel (Requires pandas and openpyxl)."""
        try:
            import pandas as pd
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False)
        except ImportError:
            raise ImportError("Excel export requires 'pandas' and 'openpyxl'. Please install them using 'pip install pandas openpyxl'.")

    @staticmethod
    def parse_csv(file_path: str) -> List[dict]:
        """Parse CSV file into list of dictionaries."""
        results = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(dict(row))
        return results

    @staticmethod
    def parse_excel(file_path: str) -> List[dict]:
        """Parse Excel file into list of dictionaries (Requires pandas and openpyxl)."""
        try:
            import pandas as pd
            df = pd.read_excel(file_path)
            # Convert NaN to None or empty string
            df = df.where(pd.notnull(df), None)
            return df.to_dict('records')
        except ImportError:
            raise ImportError("Excel import requires 'pandas' and 'openpyxl'. Please install them using 'pip install pandas openpyxl'.")
