# PharmaPOS NG - Changelog

All notable changes to PharmaPOS NG will be documented in this file.

## [2.0.0] - 2025-12-07

### Added - Market-Ready Release

#### Critical Production Features

- **Centralized Logging System**

  - Rotating file handlers for application logs
  - Separate error log file
  - Audit trail logging for user actions
  - Database operation logging

- **Backup & Recovery System**

  - Automated daily backups
  - Manual backup on-demand
  - Backup integrity verification
  - Restore from backup functionality
  - Configurable retention policy (keeps last 10 backups)
  - Backup metadata tracking

- **Customer Management**
  - Customer database with contact information
  - Purchase history tracking
  - Loyalty points system (1 point per ₦100 spent)
  - Customer search and filtering
  - Total purchases tracking

#### Business Features

- **Data Export Capabilities**

  - Export to Excel (.xlsx) with professional formatting
  - Export to PDF with styled tables
  - Export to CSV for data portability
  - Automated filename generation with timestamps

- **Enhanced Database Schema**
  - Added `customers` table with loyalty points
  - Added `customer_id` foreign key to sales table
  - Indexed customer phone and name for fast lookups
  - Sync columns for future cloud integration

#### Code Quality Improvements

- Removed all test files and development scripts
- Moved documentation to `docs/` folder
- Cleaned up temporary files and cache directories
- Updated requirements.txt with production dependencies
- Added comprehensive error handling throughout

#### Dependencies Added

- `openpyxl>=3.1.0` - Excel export functionality
- `reportlab>=4.0.0` - PDF generation
- `matplotlib>=3.8.0` - Charts and graphs (future analytics)
- `pillow>=10.0.0` - Image processing
- `cryptography>=41.0.0` - Data encryption capabilities
- `python-dotenv>=1.0.0` - Environment configuration
- `schedule>=1.2.0` - Task scheduling for automated backups

### Changed

- Reorganized project structure for production deployment
- Enhanced error messages for better user experience
- Improved logging throughout the application
- Updated README.md for customer-facing documentation

### Removed

- All test files (`test_*.py`)
- Development verification scripts (`verify_*.py`)
- Database migration scripts (replaced with migration manager)
- Temporary fix scripts (`fix_*.py`)
- Demo and quickstart scripts
- Test databases and output files
- Development cache directories (`.pytest_cache`, `.qodo`)

### Fixed

- Database schema consistency
- Foreign key relationships
- Error handling in critical operations

### Security

- Enhanced audit logging for compliance
- Prepared infrastructure for data encryption
- Session management improvements

## [1.0.0] - 2025-11-XX

### Initial Release

#### Core Features

- User authentication with role-based access control
- Point of Sale (POS) system
- Inventory management with batch tracking
- FEFO (First Expiry, First Out) principle
- Multi-store support
- Stock transfers between stores
- Sales reporting
- Receipt generation
- Thermal printer support

#### Database

- SQLite database with foreign key constraints
- Comprehensive schema for pharmacy operations
- Sync infrastructure for future cloud features

#### User Interface

- PyQt5 desktop application
- Login screen
- Dashboard with alerts
- Sales processing interface
- Inventory management screens
- Product catalog management
- Reports and analytics

---

## Version History

### Version Numbering

PharmaPOS follows Semantic Versioning (SemVer):

- **Major.Minor.Patch** (e.g., 2.0.0)
- **Major**: Breaking changes or major new features
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes and minor improvements

### Upgrade Notes

#### Upgrading from 1.x to 2.0

1. **Backup your database** before upgrading
2. The new version will automatically migrate your database schema
3. New `customers` table will be created
4. Existing sales data will be preserved
5. Default passwords should be changed immediately

### Planned Features (Roadmap)

#### Version 2.1 (Q1 2026)

- [ ] Analytics dashboard with charts
- [ ] Advanced reporting with custom date ranges
- [ ] Email/SMS notification system
- [ ] Automated reorder suggestions
- [ ] Barcode scanner integration

#### Version 2.2 (Q2 2026)

- [ ] Cloud synchronization
- [ ] Mobile app (Android/iOS)
- [ ] Multi-currency support
- [ ] Advanced user permissions
- [ ] API for third-party integrations

#### Version 3.0 (Q3 2026)

- [ ] Web-based interface
- [ ] Real-time collaboration
- [ ] Advanced analytics and forecasting
- [ ] Integration with accounting software
- [ ] Multi-language support

---

**For detailed upgrade instructions, see INSTALL.md**

**For support, contact: support@pharmapos.ng**
