import os
from datetime import datetime
from typing import Optional, List, Dict, Union

RECEIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "receipts")

try:
    # Optional dependency: python-escpos
    from escpos.printer import Usb, Network, Serial  # type: ignore
    ESC_POS_AVAILABLE = True
except Exception:
    ESC_POS_AVAILABLE = False


class ThermalPrinter:
    """Simple thermal printer helper with ESC/POS optional support.

    Backends supported:
      - FILE (fallback, default) : saves plain text receipts under `receipts/`
      - 'usb' / 'network' / 'serial' : uses python-escpos when available
      - SYSTEM : uses the system-installed printer via Qt's QPrinter (when running inside a Qt app)

    The `backend` argument may be a string (e.g. 'usb') or a dict with keys
    `{ 'type': <TYPE>, 'device_info': {...} }`.
    """

    def __init__(self, backend: Optional[Union[str, Dict]] = None, device_info: Optional[dict] = None):
        # backend: 'usb','network','serial','SYSTEM' or None
        if isinstance(backend, dict):
            self.backend_type = backend.get('type')
            self.device_info = backend.get('device_info', {})
        else:
            self.backend_type = backend
            self.device_info = device_info or {}

        self.printer = None
        self.system_mode = False

        # ESC/POS init
        if ESC_POS_AVAILABLE and self.backend_type:
            try:
                bt = str(self.backend_type).lower()
                if bt == 'usb':
                    # Accept hex strings like '0x04b8' or ints; support keys vendor_id/product_id as well
                    def _to_int(v):
                        if v is None:
                            return None
                        if isinstance(v, int):
                            return v
                        try:
                            return int(str(v), 0)
                        except Exception:
                            return None

                    v = _to_int(self.device_info.get('idVendor') or self.device_info.get('vendor_id'))
                    p = _to_int(self.device_info.get('idProduct') or self.device_info.get('product_id'))
                    if v is not None and p is not None:
                        self.printer = Usb(v, p, 0)
                    else:
                        self.printer = None
                elif bt == 'network':
                    self.printer = Network(self.device_info.get('host'))
                elif bt == 'serial':
                    # Serial device might be provided under 'devfile' or 'port'
                    dev = self.device_info.get('devfile') or self.device_info.get('port') or self.device_info.get('device')
                    baud = self.device_info.get('baudrate') or self.device_info.get('baud')
                    if dev:
                        if baud:
                            try:
                                self.printer = Serial(dev, baudrate=int(baud))
                            except Exception:
                                try:
                                    self.printer = Serial(dev)
                                except Exception:
                                    self.printer = None
                        else:
                            try:
                                self.printer = Serial(dev)
                            except Exception:
                                self.printer = None
                    else:
                        self.printer = None
            except Exception:
                self.printer = None

        # System printer support via Qt (only when backend_type == 'SYSTEM')
        if str(self.backend_type).upper() == 'SYSTEM':
            try:
                # Delay Qt imports until runtime (app may or may not be running)
                from PyQt5.QtPrintSupport import QPrinter, QPrinterInfo  # type: ignore
                from PyQt5.QtGui import QTextDocument  # type: ignore
                # store the target printer name
                self.system_printer_name = self.device_info.get('name')
                self.system_mode = True
            except Exception:
                self.system_mode = False

        # Ensure receipts dir exists
        os.makedirs(RECEIPTS_DIR, exist_ok=True)

    def print_text(self, text: str) -> dict:
        """Attempt to print text using system printer first, then fall back to other methods.

        Priority:
          1. Try system default printer via Qt (ALWAYS for best thermal printing)
          2. If ESC/POS available and configured -> send to device
          3. Fallback -> save to file
        """
        # 1) Try system default printer first (only if QApplication exists)
        try:
            from PyQt5.QtWidgets import QApplication  # type: ignore
            from PyQt5.QtPrintSupport import QPrinter, QPrinterInfo  # type: ignore
            from PyQt5.QtGui import QTextDocument  # type: ignore
            
            # Check if QApplication already exists
            app = QApplication.instance()
            if app is not None:  # Only proceed if app is running
                printers = QPrinterInfo.availablePrinters()
                if printers:
                    # Use default printer
                    printer = QPrinter(QPrinter.HighResolution)
                    default = QPrinterInfo.defaultPrinter()
                    if not default.isNull():
                        printer.setPrinterName(default.printerName())
                    
                    # Set page margins for thermal printer
                    printer.setPageMargins(5, 5, 5, 5, 1)  # 5mm margins in mm
                    
                    # Print using QTextDocument
                    doc = QTextDocument()
                    doc.setPlainText(text)
                    doc.setDefaultFont(doc.defaultFont())
                    doc.print_(printer)
                    return {"status": "printed", "device": "system_default", "path": None}
        except Exception:
            pass  # Fall through to next option

        # 2) ESC/POS via python-escpos
        if self.printer:
            try:
                self.printer.text(text)
                try:
                    self.printer.cut()
                except Exception:
                    pass
                return {"status": "printed", "device": "escpos", "path": None}
            except Exception:
                pass

        # 3) Fallback: save to file
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"receipt_{ts}.txt"
        path = os.path.abspath(os.path.join(RECEIPTS_DIR, filename))
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

        return {"status": "saved", "device": "file", "path": path}


def format_receipt(receipt_number: str, items: List[Dict], subtotal: float, tax: float, total: float,
                   payment_method: str, amount_paid: float, change: float, store: Optional[dict] = None,
                   cashier: Optional[str] = None, staff_id: Optional[str] = None) -> str:
    """Return a professional thermal receipt formatted for 80mm thermal printer.
    
    Matches standard POS receipt format with centered headers, itemized list,
    and transaction summary.
    """
    # Thermal receipt width (80mm): ~40 characters at monospace
    WIDTH = 40
    
    def center(text: str, width: int = WIDTH) -> str:
        """Center text within given width."""
        return text.center(width).rstrip()
    
    lines = []
    
    # Header
    lines.append(" " * WIDTH)  # blank line
    store_name = store.get("name") if store else "PHARMAPOS"
    lines.append(center(store_name.upper(), WIDTH))
    
    if store:
        addr = store.get("address", "").strip()
        phone = store.get("phone", "").strip()
        if addr:
            lines.append(center(addr, WIDTH))
        if phone:
            lines.append(center(f"Phone: {phone}", WIDTH))
    
    lines.append("-" * WIDTH)
    
    # Receipt info
    timestamp = datetime.now().strftime("%d/%m/%y %H:%M")
    lines.append(f"Receipt: {receipt_number}")
    lines.append(f"Date/Time: {timestamp}")
    if staff_id:
        lines.append(f"Staff ID: {staff_id}")
    if cashier:
        lines.append(f"Cashier: {cashier}")
    lines.append("-" * WIDTH)
    
    # Items header
    lines.append(f"{'Description':<25} {'Amount':>12}")
    lines.append("-" * WIDTH)
    
    # Items
    for it in items:
        name = it.get("product_name") or it.get("name") or "Item"
        qty = it.get("quantity", it.get("qty", 1))
        price = float(it.get("unit_price", it.get("price", 0.0)))
        line_total = qty * price
        
        # Truncate long names
        if len(name) > 25:
            name = name[:22] + "..."
        
        # Item line
        amount_str = f"{line_total:.2f}"
        line = f"{name:<25} {amount_str:>12}"
        lines.append(line)
    
    # Subtotals section
    lines.append("-" * WIDTH)
    lines.append(f"{'Subtotal:':<26} {subtotal:>11.2f}")
    if tax > 0:
        lines.append(f"{'Tax (VAT):':<26} {tax:>11.2f}")
    lines.append("=" * WIDTH)
    lines.append(f"{'TOTAL:':<26} {total:>11.2f}")
    lines.append("=" * WIDTH)
    
    # Payment section
    lines.append("")
    lines.append(f"{'Payment Method:':<26} {payment_method.upper():<11}")
    lines.append(f"{'Amount Paid:':<26} {amount_paid:>11.2f}")
    if change > 0.01:
        lines.append(f"{'Change:':<26} {change:>11.2f}")
    lines.append("-" * WIDTH)
    
    # Footer
    lines.append("")
    lines.append(center("Thank You for Your Purchase!", WIDTH))
    lines.append(center("Please Visit Again", WIDTH))
    lines.append("-" * WIDTH)
    lines.append("")
    
    return "\n".join(lines)
