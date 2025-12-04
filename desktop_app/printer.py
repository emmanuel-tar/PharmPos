"""
Thermal Printer Integration Module
Handles receipt printing for POS transactions via thermal printer (ESC/POS protocol).
Supports USB, Serial, and Network thermal printers.
"""

import socket
try:
    import serial  # pyserial, optional
    SERIAL_AVAILABLE = True
except Exception:
    serial = None
    SERIAL_AVAILABLE = False

try:
    import usb.core
    import usb.util
    USB_AVAILABLE = True
except Exception:
    usb = None
    USB_AVAILABLE = False
from decimal import Decimal
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class PrinterType(Enum):
    """Supported thermal printer types."""
    USB = "USB"
    SERIAL = "SERIAL"
    NETWORK = "NETWORK"
    FILE = "FILE"  # For testing - prints to file


class ThermalPrinter:
    """
    Thermal printer handler using ESC/POS protocol.
    Supports Epson TM series, Star Micronics, and compatible printers.
    """

    # ESC/POS Commands
    ESC = b'\x1b'
    GS = b'\x1d'
    NL = b'\n'
    
    # Print modes
    NORMAL = ESC + b'@'  # Initialize printer
    BOLD_ON = ESC + b'E\x01'
    BOLD_OFF = ESC + b'E\x00'
    UNDERLINE_ON = ESC + b'-\x01'
    UNDERLINE_OFF = ESC + b'-\x00'
    TEXT_CENTER = ESC + b'a\x01'
    TEXT_LEFT = ESC + b'a\x00'
    TEXT_RIGHT = ESC + b'a\x02'
    
    # Character sizes
    DOUBLE_WIDTH = ESC + b'!\x20'
    DOUBLE_HEIGHT = ESC + b'!\x10'
    LARGE = ESC + b'!\x30'  # 2x2
    NORMAL_SIZE = ESC + b'!\x00'
    
    # Paper cut
    CUT_PAPER = GS + b'V\x00'
    PARTIAL_CUT = GS + b'V\x01'

    def __init__(
        self,
        printer_type: PrinterType = PrinterType.FILE,
        port: str = "/dev/ttyUSB0",
        baudrate: int = 9600,
        host: str = "192.168.1.100",
        port_num: int = 9100,
        vendor_id: int = 0x04b8,  # Epson default
        product_id: int = 0x0202,
        output_file: str = None,
    ):
        """
        Initialize thermal printer connection.
        
        Args:
            printer_type: Type of printer (USB, SERIAL, NETWORK, FILE)
            port: Serial port (for SERIAL type)
            baudrate: Baud rate for serial connection
            host: IP address (for NETWORK type)
            port_num: Port number (for NETWORK type)
            vendor_id: USB vendor ID (for USB type)
            product_id: USB product ID (for USB type)
            output_file: Output file path (for FILE type)
        """
        self.printer_type = printer_type
        self.connection = None
        self.is_connected = False
        self.output_file = output_file or "receipt.txt"
        
        try:
            if printer_type == PrinterType.USB:
                self._connect_usb(vendor_id, product_id)
            elif printer_type == PrinterType.SERIAL:
                self._connect_serial(port, baudrate)
            elif printer_type == PrinterType.NETWORK:
                self._connect_network(host, port_num)
            elif printer_type == PrinterType.FILE:
                self.is_connected = True
                
        except Exception as e:
            print(f"Warning: Could not connect to printer: {e}")
            self.is_connected = False

    def _connect_usb(self, vendor_id: int, product_id: int) -> None:
        """Connect to USB thermal printer."""
        if not USB_AVAILABLE:
            raise Exception("USB support is not available (pyusb not installed)")

        self.connection = usb.core.find(idVendor=vendor_id, idProduct=product_id)
        if self.connection is None:
            raise Exception(f"USB Printer (VID: {hex(vendor_id)}, PID: {hex(product_id)}) not found")

        self.connection.set_configuration()
        self.is_connected = True

    def _connect_serial(self, port: str, baudrate: int) -> None:
        """Connect to Serial thermal printer."""
        if not SERIAL_AVAILABLE:
            raise Exception("Serial support is not available (pyserial not installed)")

        self.connection = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=2,
        )
        self.is_connected = True

    def _connect_network(self, host: str, port: int) -> None:
        """Connect to Network thermal printer (ESC/POS over TCP)."""
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.connect((host, port))
        self.connection.settimeout(2)
        self.is_connected = True

    def _send_command(self, data: bytes) -> None:
        """Send command/data to printer."""
        if not self.is_connected:
            return
        
        try:
            if self.printer_type == PrinterType.USB:
                self.connection.write(data)
            elif self.printer_type == PrinterType.SERIAL:
                self.connection.write(data)
            elif self.printer_type == PrinterType.NETWORK:
                self.connection.sendall(data)
            elif self.printer_type == PrinterType.FILE:
                # For testing - write to file
                with open(self.output_file, "ab") as f:
                    f.write(data)
        except Exception as e:
            print(f"Error sending to printer: {e}")

    def _write_text(self, text: str) -> None:
        """Write text to printer."""
        self._send_command(text.encode('utf-8') + self.NL)

    def print_receipt(
        self,
        receipt_number: str,
        store_name: str,
        items: List[Dict[str, Any]],
        subtotal: float,
        tax: float,
        total: float,
        payment_method: str,
        amount_paid: float,
        change: float,
        customer_name: str = "Walk-in Customer",
        cashier_name: str = "Cashier",
    ) -> bool:
        """
        Print complete sales receipt.
        
        Args:
            receipt_number: Receipt/transaction number
            store_name: Name of the store
            items: List of items sold with details
            subtotal: Subtotal before tax
            tax: Tax amount
            total: Total including tax
            payment_method: Payment method (Cash, Card, Transfer)
            amount_paid: Amount actually paid
            change: Change to return
            customer_name: Name of customer (optional)
            cashier_name: Name of cashier (optional)
            
        Returns:
            True if printing succeeded, False otherwise
        """
        if not self.is_connected and self.printer_type != PrinterType.FILE:
            print("Warning: Printer not connected, saving to file instead")
        
        try:
            # Initialize printer
            self._send_command(self.NORMAL)
            
            # Header
            self._send_command(self.TEXT_CENTER)
            self._send_command(self.BOLD_ON)
            self._write_text(store_name.upper())
            self._send_command(self.BOLD_OFF)
            
            # Receipt info
            self._send_command(self.TEXT_CENTER)
            self._write_text("=" * 40)
            self._write_text(f"Receipt #: {receipt_number}")
            self._write_text(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self._write_text(f"Customer: {customer_name}")
            self._write_text(f"Cashier: {cashier_name}")
            self._write_text("=" * 40)
            
            # Items header
            self._send_command(self.TEXT_LEFT)
            self._write_text("")
            self._write_text(f"{'Description':<25} {'Qty':>5} {'Price':>10}")
            self._write_text("-" * 40)
            
            # Items
            for item in items:
                product_name = item.get("product_name", "")[:25]
                qty = int(item.get("quantity", 0))
                unit_price = float(item.get("unit_price", 0))
                item_total = qty * unit_price
                
                self._write_text(f"{product_name:<25} {qty:>5} {item_total:>10.2f}")
            
            self._write_text("-" * 40)
            
            # Summary
            self._write_text("")
            self._send_command(self.TEXT_RIGHT)
            self._write_text(f"Subtotal:        {subtotal:>10.2f}")
            self._write_text(f"Tax (7.5%):      {tax:>10.2f}")
            self._write_text(f"Total:           {total:>10.2f}")
            self._write_text("")
            
            self._send_command(self.BOLD_ON)
            self._write_text(f"Payment: {payment_method:<15} {amount_paid:>10.2f}")
            self._send_command(self.BOLD_OFF)
            
            self._write_text(f"Change:          {change:>10.2f}")
            
            # Footer
            self._write_text("")
            self._send_command(self.TEXT_CENTER)
            self._write_text("Thank you for your purchase!")
            self._write_text("Please come again!")
            self._write_text("")
            
            # Cut paper
            self._send_command(self.CUT_PAPER)
            
            # Print additional newlines for next receipt
            for _ in range(5):
                self._write_text("")
            
            return True
            
        except Exception as e:
            print(f"Error printing receipt: {e}")
            return False

    def print_simple_receipt(
        self,
        receipt_data: str,
    ) -> bool:
        """
        Print simple text receipt directly.
        
        Args:
            receipt_data: Pre-formatted receipt text
            
        Returns:
            True if printing succeeded, False otherwise
        """
        try:
            self._send_command(self.NORMAL)
            self._write_text(receipt_data)
            self._send_command(self.CUT_PAPER)
            return True
        except Exception as e:
            print(f"Error printing receipt: {e}")
            return False

    def close(self) -> None:
        """Close printer connection."""
        try:
            if self.connection:
                if self.printer_type == PrinterType.SERIAL:
                    self.connection.close()
                elif self.printer_type == PrinterType.NETWORK:
                    self.connection.close()
                # USB connections are typically closed by garbage collection
            
            self.is_connected = False
        except Exception as e:
            print(f"Error closing printer: {e}")


class ReceiptGenerator:
    """Helper class to format receipt data."""
    
    @staticmethod
    def format_receipt_text(
        receipt_number: str,
        store_name: str,
        items: List[Dict[str, Any]],
        subtotal: float,
        tax: float,
        total: float,
        payment_method: str,
        amount_paid: float,
        change: float,
        customer_name: str = "Walk-in Customer",
        cashier_name: str = "Cashier",
        paper_width: int = 40,
    ) -> str:
        """Generate formatted receipt text."""
        
        lines = []
        
        # Header
        lines.append(store_name.upper().center(paper_width))
        lines.append("=" * paper_width)
        lines.append(f"Receipt #: {receipt_number}")
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Customer: {customer_name}")
        lines.append(f"Cashier: {cashier_name}")
        lines.append("=" * paper_width)
        lines.append("")
        
        # Items header
        lines.append(f"{'Description':<25} {'Qty':>5} {'Price':>10}")
        lines.append("-" * paper_width)
        
        # Items
        for item in items:
            product_name = item.get("product_name", "")[:25]
            qty = int(item.get("quantity", 0))
            unit_price = float(item.get("unit_price", 0))
            item_total = qty * unit_price
            
            lines.append(f"{product_name:<25} {qty:>5} {item_total:>10.2f}")
        
        lines.append("-" * paper_width)
        lines.append("")
        
        # Summary (right-aligned)
        lines.append(f"{'Subtotal:':<30} {subtotal:>10.2f}")
        lines.append(f"{'Tax (7.5%):':<30} {tax:>10.2f}")
        lines.append(f"{'Total:':<30} {total:>10.2f}")
        lines.append("")
        lines.append(f"{'Payment (' + payment_method + '):':<30} {amount_paid:>10.2f}")
        lines.append(f"{'Change:':<30} {change:>10.2f}")
        
        # Footer
        lines.append("")
        lines.append("Thank you for your purchase!".center(paper_width))
        lines.append("Please come again!".center(paper_width))
        lines.append("")
        
        return "\n".join(lines)


if __name__ == "__main__":
    # Test: Print sample receipt to file
    printer = ThermalPrinter(
        printer_type=PrinterType.FILE,
        output_file="sample_receipt.txt"
    )
    
    sample_items = [
        {"product_name": "Paracetamol 500mg", "quantity": 2, "unit_price": 150.00},
        {"product_name": "Amoxicillin 250mg", "quantity": 1, "unit_price": 100.00},
        {"product_name": "Ibuprofen 400mg", "quantity": 3, "unit_price": 80.00},
    ]
    
    subtotal = 640.00
    tax = subtotal * 0.075
    total = subtotal + tax
    
    printer.print_receipt(
        receipt_number="REC-001",
        store_name="PharmaPOS Store",
        items=sample_items,
        subtotal=subtotal,
        tax=tax,
        total=total,
        payment_method="Cash",
        amount_paid=700.00,
        change=700.00 - total,
        customer_name="John Doe",
        cashier_name="Cashier 1",
    )
    
    print("Sample receipt printed to sample_receipt.txt")
