# PharmaPOS NG - Professional Pharmacy Management System

**Version 2.0.0** | **Market-Ready Release**

A complete, production-ready pharmacy billing and inventory management system built with Python, SQLAlchemy, and PyQt5. Designed specifically for Nigerian pharmacies with NAFDAC compliance, FEFO inventory management, and comprehensive reporting.

---

## 🌟 Key Features

### 💼 Business Management

- **Point of Sale (POS)** - Fast, intuitive sales interface with multiple payment methods
- **Customer Management** - Track customer purchases and loyalty points
- **Inventory Control** - Batch-based tracking with FEFO (First Expiry, First Out)
- **Multi-Store Support** - Manage multiple pharmacy locations
- **Comprehensive Reporting** - Sales, inventory, and compliance reports

### 🔒 Security & Compliance

- **Role-Based Access** - Admin, Manager, and Cashier roles
- **Audit Trail** - Complete logging of all transactions
- **NAFDAC Compliance** - Track regulatory information
- **Secure Authentication** - Password hashing with PBKDF2
- **Automated Backups** - Daily backups with restore capability

### 📊 Advanced Features

- **FEFO Inventory** - Automatic expiry-based stock rotation
- **Batch Tracking** - Complete traceability of all stock movements
- **Expiry Alerts** - Notifications for expiring products
- **Low Stock Alerts** - Automated reorder notifications
- **Data Export** - Export to Excel, PDF, and CSV
- **Loyalty Program** - Built-in customer rewards system

### 🖨️ Hardware Integration

- **Thermal Printer Support** - POS receipt printers
- **System Printer** - Standard Windows printers
- **Barcode Ready** - Prepared for scanner integration

---

## 📋 System Requirements

### Minimum

- Windows 10 (64-bit)
- Intel Core i3 or equivalent
- 4 GB RAM
- 500 MB free storage
- 1280x720 display

### Recommended

- Windows 10/11 (64-bit)
- Intel Core i5 or better
- 8 GB RAM
- 2 GB free storage
- 1920x1080 display

---

## 🚀 Quick Start

### 1. Install Python

Download Python 3.11+ from [python.org](https://www.python.org/downloads/)

**Important**: Check "Add Python to PATH" during installation

### 2. Install PharmaPOS

```bash
# Extract PharmaPOS to your desired location
cd C:\PharmaPOS

# Install dependencies
pip install -r requirements.txt

# Initialize database
python install.py --init-db

# Launch application
python app.py
```

### 3. First Login

**Default Credentials:**

- Admin: `admin` / `admin123`
- Manager: `manager1` / `manager123`
- Cashier: `cashier1` / `cashier123`

⚠️ **Change these passwords immediately after first login!**

---

## 📖 Documentation

- **[Installation Guide](INSTALL.md)** - Detailed setup instructions
- **[Changelog](CHANGELOG.md)** - Version history and updates
- **[User Manual](docs/)** - Complete user documentation
- **[License](LICENSE.txt)** - Terms and conditions

---

## 💡 Core Capabilities

### Sales Management

- Shopping cart with real-time totals
- Multiple payment methods (Cash, Card, Transfer, Paystack, Flutterwave)
- Automatic receipt generation
- Customer selection and loyalty points
- Change calculation
- Payment reference tracking

### Inventory Management

- Product catalog with SKU and barcode
- Batch-based stock tracking
- FEFO automatic allocation
- Stock receiving with expiry dates
- Inter-store transfers
- Stock adjustments and write-offs
- Inventory reconciliation
- Comprehensive audit trail

### Customer Management

- Customer database with contact info
- Purchase history tracking
- Loyalty points (1 point per ₦100)
- Customer search and filtering
- Total purchases tracking

### Reporting & Analytics

- Daily sales reports
- Top-selling products
- Inventory valuation
- Batch aging analysis
- Expiry alerts
- Low stock alerts
- Cashier performance
- Export to Excel/PDF/CSV

### Multi-Store Operations

- Multiple pharmacy locations
- Per-store inventory
- Stock transfers between stores
- Centralized reporting
- Store-specific user assignments

---

## 🔐 Security Features

- **Password Security**: PBKDF2 hashing with 100,000 iterations
- **Session Management**: Automatic timeout after 60 minutes
- **Audit Logging**: All critical operations logged
- **Role-Based Access**: Granular permission control
- **Data Backup**: Automated daily backups
- **Data Encryption**: Infrastructure for sensitive data

---

## 📊 Data Management

### Automated Backups

- Daily automatic backups
- Manual backup on-demand
- Backup verification
- Easy restore process
- Configurable retention (default: 10 backups)

### Data Export

- **Excel**: Professional formatted reports
- **PDF**: Styled documents with tables
- **CSV**: Universal data format
- Automatic timestamp naming

---

## 🛠️ Technical Stack

### Core Technologies

- **Python 3.8+** - Programming language
- **SQLAlchemy 2.0** - Database ORM
- **PyQt5** - Desktop UI framework
- **SQLite** - Embedded database

### Additional Libraries

- **openpyxl** - Excel generation
- **reportlab** - PDF creation
- **matplotlib** - Charts and graphs
- **cryptography** - Data security
- **Pillow** - Image processing

---

## 📞 Support

### Getting Help

- **Email**: support@pharmapos.ng
- **Website**: www.pharmapos.ng
- **Documentation**: See `docs/` folder
- **Logs**: Check `logs/` folder for troubleshooting

### Common Issues

See [INSTALL.md](INSTALL.md) for troubleshooting guide

---

## 🔄 Updates

### Checking for Updates

1. Go to Help → Check for Updates
2. Download latest version
3. Backup your database
4. Install new version

### Version History

See [CHANGELOG.md](CHANGELOG.md) for complete version history

---

## 📜 License

PharmaPOS NG is licensed software. See [LICENSE.txt](LICENSE.txt) for full terms and conditions.

**Copyright © 2025 PharmaPOS NG. All rights reserved.**

---

## 🎯 Designed for Nigerian Pharmacies

- NAFDAC number tracking
- Nigerian Naira (₦) currency
- Local compliance features
- Multi-store management
- FEFO inventory control
- Comprehensive audit trails

---

## 🚦 Getting Started Checklist

- [ ] Install Python 3.11+
- [ ] Install PharmaPOS dependencies
- [ ] Initialize database
- [ ] Login and change default passwords
- [ ] Configure store information
- [ ] Add products to catalog
- [ ] Receive opening inventory
- [ ] Configure printer (optional)
- [ ] Create user accounts
- [ ] Test backup and restore
- [ ] Start selling!

---

## 📈 What's New in Version 2.0

### Major Enhancements

✅ Customer management with loyalty points  
✅ Automated backup and recovery system  
✅ Data export (Excel, PDF, CSV)  
✅ Centralized logging and error tracking  
✅ Production-ready codebase  
✅ Comprehensive documentation  
✅ Enhanced security features

See [CHANGELOG.md](CHANGELOG.md) for complete details.

---

## 🤝 Professional Support

For enterprise deployments, custom features, or training:

- **Email**: sales@pharmapos.ng
- **Phone**: [Contact number]
- **Website**: www.pharmapos.ng

---

**Built with ❤️ for Nigerian Pharmacies**

_PharmaPOS NG - Simplifying Pharmacy Management_
