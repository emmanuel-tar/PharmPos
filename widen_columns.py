import sys

# Read the file
with open('desktop_app/ui.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and replace the column width lines
modified = False
for i, line in enumerate(lines):
    # Products table Name column
    if 'self.products_table.setColumnWidth(1, 120)' in line:
        lines[i] = '        self.products_table.setColumnWidth(1, 250)  # Product Name - wider\n'
        modified = True
        print(f"Line {i+1}: Changed products Name column width from 120 to 250")
    
    # Products table SKU column
    elif 'self.products_table.setColumnWidth(2, 80)' in line:
        lines[i] = '        self.products_table.setColumnWidth(2, 120)  # SKU - wider\n'
        modified = True
        print(f"Line {i+1}: Changed products SKU column width from 80 to 120")
    
    # Sales cart Product column
    elif 'self.sales_cart_table.setColumnWidth(1, 160)' in line:
        lines[i] = '        self.sales_cart_table.setColumnWidth(1, 280)  # Product - wider\n'
        modified = True
        print(f"Line {i+1}: Changed sales cart Product column width from 160 to 280")

if modified:
    # Write the file back
    with open('desktop_app/ui.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("\nSuccessfully updated column widths!")
else:
    print("No matching lines found to modify")
