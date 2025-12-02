# PharmaPOS NG - Pharmacy Management System

A complete pharmacy billing and inventory management system built with Python, SQLAlchemy, and PyQt5.

## Features

### 1. **Authentication & User Management**
- User registration and login with password hashing (PBKDF2)
- Role-based access control (Admin, Manager, Cashier)
- Session management with automatic timeout
- Password change functionality

### 2. **Point of Sale (POS)**
- Fast and intuitive sales interface
- Shopping cart system
- Multiple payment methods (Cash, Card, Transfer)
- Automatic receipt generation
- Change calculation

### 3. **Inventory Management**
- Product catalog with SKU and barcode support
- Batch-based inventory tracking
- **FEFO (First Expiry, First Out)** principle
- Stock level monitoring
- Batch expiry tracking
- Automatic audit trail for all stock movements

### 4. **Multi-Store Operations**
- Support for multiple pharmacy locations
- Per-store user assignments
- Inter-store stock transfers
- Centralized reporting

### 5. **Stock Management**
- Stock receipt and recording
- Real-time stock level updates
- Stock transfers between stores
- Batch write-offs and adjustments
- Complete inventory audit trail

### 6. **Reporting & Analytics**
- Daily sales reports
- Top-selling products analysis
- Inventory valuation reports
- Batch aging analysis
- Complete audit trails
- Expiry alerts
- Low stock alerts

## Project Structure

```
PharmPos/
├── install.py                 # Dependency installer with DB initialization
├── requirements.txt           # Python dependencies
├── app.py                     # Main application entry point
├── demo.py                    # Demo script to test functionality
├── pharmapos.db              # SQLite database (created on first run)
└── desktop_app/
    ├── database.py           # Database schema and initialization
    ├── models.py             # ORM models and business logic services
    ├── auth.py               # Authentication and session management
    ├── sales.py              # Sales transaction processing
    ├── inventory.py          # Inventory management and batch tracking
    ├── reports.py            # Reporting and analytics
    └── ui.py                 # PyQt5 desktop application UI
```

## Installation

### 1. Install Dependencies

```bash
python install.py
```

Or manually:
```bash
pip install -r requirements.txt
python install.py --init-db
```

### 2. Initialize Database

```bash
python install.py --init-db
```

Or with custom database path:
```bash
python install.py --init-db --db ./data/pharmacy.db
```

## Usage

### Run Demo Script

Test all functionality without the GUI:
```bash
python demo.py
```

The demo will:
- Create sample data (stores, users, products)
- Demonstrate authentication
- Process sample sales transactions
- Show inventory management
- Display alerts and reports

### Run Desktop Application

```bash
python app.py
```

This opens the PyQt5 desktop application with:
- Login screen
- Dashboard with alerts
- Sales processing interface
- Inventory management
- Product catalog
- Reports and analytics

## Database Schema

### Core Tables

| Table | Purpose |
|-------|---------|
| `stores` | Multiple pharmacy locations |
| `users` | Staff accounts with roles |
| `products` | Product master catalog |
| `product_batches` | Inventory batches with expiry tracking |
| `sales` | Completed transactions |
| `sale_items` | Individual items in sales |
| `stock_transfers` | Inter-store stock movements |
| `inventory_audit` | Complete audit trail |

### Key Features

- **Foreign Key Constraints**: Ensures data integrity
- **FEFO Support**: Batches ordered by expiry date for automatic FEFO picking
- **Audit Trail**: Every inventory change is logged with user, timestamp, and reason
- **Indexes**: Performance optimization on frequently queried fields
- **Partial Unique Index**: Ensures only one primary store

## API Examples

### Authentication

```python
from desktop_app.auth import AuthenticationService

auth = AuthenticationService()

# Register user
auth.register_user("cashier1", "password123", role="cashier")

# Login
session = auth.login("cashier1", "password123")
if session:
    print(f"Logged in as: {session.username}")
```

### Sales Processing

```python
from desktop_app.sales import SalesTransaction

sales = SalesTransaction()

# Add items to cart
success, msg, cart = sales.add_item_to_cart([], batch_id=1, quantity=5)

# Complete sale
success, msg, sale = sales.finalize_sale(
    user_id=1,
    store_id=1,
    cart=cart,
    payment_method="cash",
    amount_paid=Decimal("1000")
)
```

### Inventory Management

```python
from desktop_app.inventory import BatchManager, InventoryAlerts

# Receive stock
batch_manager = BatchManager()
success, msg, batch = batch_manager.receive_batch(
    product_id=1,
    store_id=1,
    batch_number="BATCH-001",
    quantity=100,
    expiry_date=date(2026, 12, 31),
    cost_price=Decimal("50")
)

# Check alerts
alerts = InventoryAlerts()
report = alerts.generate_alerts(store_id=1)
```

### Reporting

```python
from desktop_app.reports import SalesReporter, InventoryReporter

# Sales report
sales_reporter = SalesReporter()
daily_sales = sales_reporter.get_daily_sales(store_id=1, report_date=date.today())

# Inventory report
inventory_reporter = InventoryReporter()
valuation = inventory_reporter.get_stock_valuation(store_id=1)
```

## Configuration

### Password Security

Passwords are hashed using PBKDF2 with:
- Algorithm: SHA256
- Iterations: 100,000
- Salt: 16 random bytes

### Session Management

- Session timeout: 60 minutes (configurable)
- Sessions stored in-memory during application runtime
- Automatic cleanup of expired sessions

### Database

- Default database: `pharmapos.db` (SQLite)
- Foreign keys enabled by default
- Automatic timestamp management

## Compliance

### Pharmaceutical Features

- **NAFDAC Number**: Tracks regulatory compliance for each product
- **Batch Tracking**: Complete traceability of stock movements
- **FEFO Principle**: Ensures oldest stock sells first
- **Expiry Management**: Automatic alerts for expiring products
- **Audit Trail**: Complete record of all inventory changes

## Advanced Features

### FEFO Implementation

The system automatically:
1. Sorts batches by expiry date when picking
2. Suggests the oldest batch for sale
3. Prevents selling expired products
4. Generates expiry alerts

### Multi-User Workflow

- Admin: Full system access, user management
- Manager: Store-level reporting and approval
- Cashier: Sales transactions and stock receiving

### Reporting Flexibility

- Daily, weekly, monthly sales summaries
- Top-selling products analysis
- Inventory valuation by cost
- Batch aging reports
- Complete audit trails for compliance

## Troubleshooting

### Database Issues

If database is corrupted:
```bash
rm pharmapos.db
python install.py --init-db
```

### Import Errors

Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### UI Issues

PyQt5 may require additional system libraries on Linux:
```bash
sudo apt-get install python3-pyqt5
```

## Future Enhancements

- Cloud synchronization
- Barcode scanning integration
- Mobile app
- Advanced reporting with charts
- SMS alerts for low stock
- Automated reordering
- Integration with payment gateways
- Multi-language support

## Support

For issues or questions, refer to the demo script for usage examples.

## License

PharmaPOS NG is provided as-is for pharmacy management operations.
