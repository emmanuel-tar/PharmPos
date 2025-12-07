import sys

# Read the file
with open('desktop_app/ui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the import section
old_import = """    QCheckBox,
)
from PyQt5.QtCore import Qt, QDate"""

new_import = """    QCheckBox,
    QShortcut,
)
from PyQt5.QtCore import Qt, QDate"""

content = content.replace(old_import, new_import)

# Write the file back
with open('desktop_app/ui.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully added QShortcut import")
