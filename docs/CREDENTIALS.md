# 🔐 PharmaPOS NG - Login Credentials

## Default Test Users

These are the default users created when you run `python demo.py`:

| Username | Password | Role | Description |
|----------|----------|------|-------------|
| **admin** | **admin123** | Admin | Full system access, create users, manage stores |
| **manager1** | **manager123** | Manager | Inventory and sales management |
| **cashier1** | **cashier123** | Cashier | Sales processing only |

---

## Login Interface

The login screen now features:

✅ **Username Dropdown** - Select from available users
✅ **Password Field** - Enter user password
✅ **Auto-loading** - Automatically loads active users from database

---

## How to Use

### Method 1: Interactive Setup
```bash
python quickstart.py
# Select "Run demo" to create test users
# Then select "Launch app"
```

### Method 2: Direct Launch
```bash
python demo.py          # Creates test database with users
python app.py           # Launch the app and login
```

### Method 3: First Time Setup
```bash
python install.py --init-db    # Initialize database
# Use credentials above to login
```

---

## Adding New Users

To add new users, use the admin account:

1. Login as **admin** with password **admin123**
2. Navigate to the application's user management section
3. Create new users with custom roles

---

## Password Security

All passwords are secured using:

- **PBKDF2-SHA256** hashing algorithm
- **100,000 iterations** for enhanced security
- **Random salt** per password
- **Plaintext never stored** - only hashes

---

## Default Passwords Explained

- **admin123** - Easy to remember for demo/testing
- **manager123** - Different password for different role
- **cashier123** - Separate credentials for cashier access

⚠️ **IMPORTANT:** Change these passwords in production!

---

## Forgot Password?

If you forget the admin password:

1. Delete `pharmapos.db`
2. Run `python install.py --init-db` to recreate with defaults
3. Or modify database directly using SQLite tools

---

## Demo Data

When you run `python demo.py`, it creates:

- ✅ Sample stores (Head Office, Branch 1, Branch 2)
- ✅ Test users (admin, manager1, cashier1)
- ✅ Sample products (Paracetamol, Amoxicillin, etc.)
- ✅ Stock batches with expiry dates
- ✅ Sample sales transactions

Then you can login and explore all features!

---

## Quick Login Flow

1. **Start app**: `python app.py`
2. **Select username** from dropdown (e.g., "admin")
3. **Enter password** (e.g., "admin123")
4. **Click Login**
5. **Explore the system!**

---

## Testing Different Roles

### As Admin (admin/admin123):
- Create stores and users
- View all reports
- Manage system settings

### As Manager (manager1/manager123):
- Receive inventory
- Process sales
- View inventory reports

### As Cashier (cashier1/cashier123):
- Process sales only
- Limited inventory view
- No report access

---

## Database Users Query

To see all users in the database:

```bash
sqlite3 pharmapos.db "SELECT username, role FROM users WHERE is_active=1;"
```

---

**Created:** December 1, 2025
**System:** PharmaPOS NG v1.0.0
