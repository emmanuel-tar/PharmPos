# PharmaPOS NG - Installation Guide

## System Requirements

### Minimum Requirements

- **Operating System**: Windows 10 or later (64-bit)
- **Processor**: Intel Core i3 or equivalent
- **RAM**: 4 GB
- **Storage**: 500 MB free space (plus space for database)
- **Display**: 1280x720 resolution or higher
- **Python**: Python 3.8 or later

### Recommended Requirements

- **Operating System**: Windows 10/11 (64-bit)
- **Processor**: Intel Core i5 or better
- **RAM**: 8 GB or more
- **Storage**: 2 GB free space
- **Display**: 1920x1080 resolution
- **Network**: Internet connection (for updates and cloud sync)

## Installation Steps

### Step 1: Install Python

1. Download Python 3.11 or later from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. **Important**: Check "Add Python to PATH" during installation
4. Verify installation by opening Command Prompt and typing:
   ```
   python --version
   ```

### Step 2: Download PharmaPOS

1. Download the PharmaPOS package
2. Extract to a location like `C:\PharmaPOS`
3. Open Command Prompt in the PharmaPOS directory

### Step 3: Install Dependencies

Run the following command:

```bash
pip install -r requirements.txt
```

This will install all required packages:

- SQLAlchemy (database)
- PyQt5 (user interface)
- openpyxl (Excel export)
- reportlab (PDF generation)
- matplotlib (charts)
- And other dependencies

### Step 4: Initialize Database

Run the installation script:

```bash
python install.py --init-db
```

This will:

- Create the database
- Set up all tables
- Create default users:
  - **Username**: `admin` | **Password**: `admin123` (Admin)
  - **Username**: `manager1` | **Password**: `manager123` (Manager)
  - **Username**: `cashier1` | **Password**: `cashier123` (Cashier)

**IMPORTANT**: Change these default passwords immediately after first login!

### Step 5: Launch Application

Start the application:

```bash
python app.py
```

Or double-click `app.py` if Python is properly associated.

## First-Time Setup

### 1. Login

- Use the admin account (admin/admin123)
- You'll be prompted to change your password

### 2. Configure Store Information

- Go to Settings → Store Management
- Update your pharmacy details:
  - Store name
  - Address
  - Phone number
  - Email

### 3. Add Products

- Go to Inventory → Products
- Add your product catalog
- Include:
  - Product name
  - SKU
  - NAFDAC number
  - Pricing information

### 4. Receive Initial Stock

- Go to Inventory → Receive Stock
- Record your opening inventory
- Include batch numbers and expiry dates

### 5. Configure Printer (Optional)

- Go to Settings → Printer Settings
- Configure your receipt printer
- Test printing

### 6. Create Users

- Go to Settings → User Management
- Create accounts for your staff
- Assign appropriate roles:
  - **Admin**: Full access
  - **Manager**: Reports and inventory
  - **Cashier**: Sales only

## Configuration

### Printer Setup

PharmaPOS supports multiple printer types:

1. **System Printer** (Recommended for Windows)

   - Select from installed printers
   - Works with any Windows-compatible printer

2. **Thermal Printer** (POS Printers)

   - USB connection
   - Serial port connection
   - Network connection

3. **File Output** (Testing)
   - Saves receipts as text files

### Backup Configuration

Automatic backups are enabled by default:

- **Frequency**: Daily
- **Location**: `./backups` folder
- **Retention**: Last 10 backups

To change backup settings:

1. Go to Settings → Backup
2. Configure schedule and location
3. Test backup/restore

### Environment Variables (Optional)

Create a `.env` file in the application directory for advanced configuration:

```env
# Database
DB_PATH=pharmapos.db

# Backup
BACKUP_INTERVAL_HOURS=24
BACKUP_RETENTION_COUNT=10

# Payment Gateways (if using online payments)
PAYSTACK_PUBLIC_KEY=pk_live_xxxxx
PAYSTACK_SECRET_KEY=sk_live_xxxxx

# Email Notifications (if enabled)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# SMS Notifications (if enabled)
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_PHONE_NUMBER=+1234567890
```

## Troubleshooting

### Application Won't Start

**Problem**: Double-clicking app.py doesn't work
**Solution**:

1. Open Command Prompt
2. Navigate to PharmaPOS folder
3. Run: `python app.py`
4. Check for error messages

**Problem**: "Python not found"
**Solution**:

1. Reinstall Python
2. Ensure "Add to PATH" is checked
3. Restart computer

### Database Errors

**Problem**: "Database is locked"
**Solution**:

1. Close all PharmaPOS windows
2. Restart the application
3. If persists, restart computer

**Problem**: "Table not found"
**Solution**:

1. Run: `python install.py --init-db`
2. This will recreate database tables

### Printer Issues

**Problem**: Receipts not printing
**Solution**:

1. Check printer is powered on and connected
2. Verify printer settings in application
3. Test with Windows test page first
4. Check printer drivers are installed

**Problem**: Garbled text on receipt
**Solution**:

1. Check character encoding settings
2. Update printer drivers
3. Try different printer type in settings

### Performance Issues

**Problem**: Application is slow
**Solution**:

1. Check database size (Settings → Database Info)
2. Run cleanup: Remove old audit logs
3. Optimize database: Settings → Maintenance → Optimize
4. Close other applications

## Data Management

### Backup

**Manual Backup**:

1. Go to Settings → Backup
2. Click "Create Backup Now"
3. Save backup file to safe location (USB drive, cloud storage)

**Restore from Backup**:

1. Go to Settings → Backup
2. Click "Restore from Backup"
3. Select backup file
4. Confirm restoration

**IMPORTANT**: Always backup before:

- Software updates
- Major data changes
- System maintenance

### Data Export

Export data for reporting or migration:

1. **Sales Reports**: Sales → Reports → Export
2. **Inventory**: Inventory → Export to Excel/PDF
3. **Customer Data**: Customers → Export

Supported formats:

- Excel (.xlsx)
- PDF
- CSV

## Updates

### Checking for Updates

1. Go to Help → Check for Updates
2. Follow prompts to download and install

### Manual Update

1. Backup your database
2. Download latest version
3. Extract to new folder
4. Copy `pharmapos.db` from old installation
5. Run new version

## Security Best Practices

1. **Change Default Passwords**

   - Change all default user passwords immediately
   - Use strong passwords (8+ characters, mixed case, numbers)

2. **User Access Control**

   - Only create necessary user accounts
   - Assign minimum required permissions
   - Disable unused accounts

3. **Regular Backups**

   - Enable automatic backups
   - Store backups in multiple locations
   - Test restore procedure regularly

4. **Physical Security**

   - Lock computer when away
   - Restrict physical access to server
   - Use screen lock timeout

5. **Network Security** (if applicable)
   - Use firewall
   - Keep Windows updated
   - Use antivirus software

## Getting Help

### Documentation

- User Manual: `docs/user_manual.md`
- FAQ: `docs/FAQ.md`
- Video Tutorials: [Link to videos]

### Support

- Email: support@pharmapos.ng
- Phone: [Support number]
- Website: www.pharmapos.ng

### Logs

For troubleshooting, check log files:

- Location: `logs/` folder
- `pharmapos.log`: All application logs
- `errors.log`: Error messages only

Send log files to support when reporting issues.

## Uninstallation

To remove PharmaPOS:

1. **Backup your data** (if you want to keep it)
2. Close the application
3. Delete the PharmaPOS folder
4. (Optional) Uninstall Python if not needed for other applications

## License

PharmaPOS NG is licensed software. See LICENSE.txt for terms and conditions.

## Contact

For sales, licensing, or general inquiries:

- Email: info@pharmapos.ng
- Website: www.pharmapos.ng
- Phone: [Contact number]

---

**Version**: 2.0.0  
**Last Updated**: December 2025  
**Copyright**: © 2025 PharmaPOS NG. All rights reserved.
