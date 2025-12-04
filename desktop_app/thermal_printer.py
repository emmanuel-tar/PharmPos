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
                    self.printer = Usb(self.device_info.get('idVendor'), self.device_info.get('idProduct'), 0)
                elif bt == 'network':
                    self.printer = Network(self.device_info.get('host'))
                elif bt == 'serial':
                    self.printer = Serial(self.device_info.get('devfile'))
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
        """Attempt to print plain text; returns info dict with status.

        Priority:
          1. If system printer requested and Qt printing available -> use system printer
          2. If ESC/POS available and configured -> send to device
          3. Fallback -> save to file
        """
        # 1) System printer via Qt
        if self.system_mode:
            try:
                from PyQt5.QtPrintSupport import QPrinter, QPrinterInfo  # type: ignore
                from PyQt5.QtGui import QTextDocument  # type: ignore
                # create printer and set to named one if provided
                printer = QPrinter()
                if self.system_printer_name:
                    # Ensure this printer exists
                    available = [p.printerName() for p in QPrinterInfo.availablePrinters()]
                    if self.system_printer_name in available:
                        printer.setPrinterName(self.system_printer_name)
                # Use QTextDocument to print plain text
                doc = QTextDocument()
                doc.setPlainText(text)
                doc.print_(printer)
                return {"status": "printed", "path": None}
            except Exception:
                # fall through to next option
                pass

        # 2) ESC/POS
        if self.printer:
            try:
                self.printer.text(text)
                try:
                    self.printer.cut()
                except Exception:
                    pass
                return {"status": "printed", "path": None}
            except Exception:
                pass

        # 3) Fallback: save to file
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"receipt_{ts}.txt"
        path = os.path.abspath(os.path.join(RECEIPTS_DIR, filename))
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

        return {"status": "saved", "path": path}


def format_receipt(receipt_number: str, items: List[Dict], subtotal: float, tax: float, total: float,
                   payment_method: str, amount_paid: float, change: float, store: Optional[dict] = None) -> str:
    """Return a plain-text formatted receipt suitable for thermal printing."""
    lines = []
    header = store.get("name") if store else "PharmaPOS"
    lines.append(header)
    if store:
        addr = store.get("address")
        if addr:
            lines.append(addr)
    lines.append("-")
    lines.append(f"Receipt #: {receipt_number}")
    lines.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    lines.append("-")

    for it in items:
        name = it.get("product_name") or it.get("name") or "Item"
        qty = it.get("quantity", it.get("qty", 1))
        price = it.get("unit_price", it.get("price", 0.0))
        line_total = qty * float(price)
        lines.append(f"{name}")
        lines.append(f"  {qty} x {price:.2f} = {line_total:.2f}")

    lines.append("-")
    lines.append(f"Subtotal: {subtotal:.2f}")
    lines.append(f"Tax: {tax:.2f}")
    lines.append(f"Total: {total:.2f}")
    lines.append(f"Payment: {payment_method}")
    lines.append(f"Paid: {amount_paid:.2f}")
    lines.append(f"Change: {change:.2f}")
    lines.append("-")
    lines.append("Thank you for your purchase!")
    lines.append("")
    return "\n".join(lines)
