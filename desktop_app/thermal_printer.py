import os
from datetime import datetime
from typing import Optional, List, Dict

RECEIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "receipts")

try:
    # Optional dependency: python-escpos
    from escpos.printer import Usb, Network, Serial  # type: ignore
    ESC_POS_AVAILABLE = True
except Exception:
    ESC_POS_AVAILABLE = False


class ThermalPrinter:
    """Simple thermal printer helper with ESC/POS optional support.

    If an ESC/POS printer is not available or not configured this will
    fall back to saving a plain-text receipt under `receipts/`.
    """

    def __init__(self, backend: Optional[str] = None, device_info: Optional[dict] = None):
        # backend: 'usb', 'network', 'serial' or None
        self.backend = backend
        self.device_info = device_info or {}

        self.printer = None
        if ESC_POS_AVAILABLE and backend:
            try:
                if backend == "usb":
                    self.printer = Usb(
                        self.device_info.get("idVendor"),
                        self.device_info.get("idProduct"),
                        0,
                    )
                elif backend == "network":
                    self.printer = Network(self.device_info.get("host"))
                elif backend == "serial":
                    self.printer = Serial(self.device_info.get("devfile"))
            except Exception:
                # If ESC/POS backend init fails, fallback to file mode
                self.printer = None

        # Ensure receipts dir exists
        os.makedirs(RECEIPTS_DIR, exist_ok=True)

    def print_text(self, text: str) -> dict:
        """Attempt to print plain text; returns info dict with status.

        If ESC/POS is available and printer configured the text will be
        sent to the device. Otherwise the text is saved to a timestamped
        file in `receipts/` and the path returned.
        """
        if self.printer:
            try:
                # Use simple text printing; advanced formats may be added
                self.printer.text(text)
                try:
                    self.printer.cut()
                except Exception:
                    pass
                return {"status": "printed", "path": None}
            except Exception as e:
                # fallback to saving file
                pass

        # Fallback: save to file
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
