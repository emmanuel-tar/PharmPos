"""
PharmaPOS Reusable UI Components

This module contains reusable UI components and widgets to promote
code reuse and maintain consistency across the application.
"""

from typing import Optional, Callable, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QProgressBar, QFrame, QGroupBox,
    QTextEdit, QCheckBox, QRadioButton, QButtonGroup, QMessageBox,
    QInputDialog, QDialog, QFormLayout, QSplitter, QTabWidget,
    QScrollArea, QGridLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap

from .ui_constants import Colors, Fonts, Dimensions, Styles, Messages


class LoadingIndicator(QWidget):
    """A loading indicator widget with spinner animation."""

    def __init__(self, message: str = "Loading...", parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 100)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Loading label
        self.label = QLabel(message)
        self.label.setFont(Fonts.BODY)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate progress
        self.progress.setFixedWidth(150)
        layout.addWidget(self.progress, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def set_message(self, message: str):
        """Update the loading message."""
        self.label.setText(message)


class Card(QFrame):
    """A card widget with rounded corners and shadow effect."""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet(Styles.card())
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(15, 15, 15, 15)

        if title:
            title_label = QLabel(title)
            title_label.setFont(Fonts.SUBTITLE)
            title_label.setStyleSheet(f"color: {Colors.PRIMARY}; margin-bottom: 10px;")
            self.layout.addWidget(title_label)

        self.setLayout(self.layout)

    def add_widget(self, widget: QWidget):
        """Add a widget to the card."""
        self.layout.addWidget(widget)

    def add_layout(self, layout):
        """Add a layout to the card."""
        self.layout.addLayout(layout)


class FormField(QWidget):
    """A form field with label and input widget."""

    def __init__(self, label_text: str, input_widget: QWidget, required: bool = False, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Label
        label = QLabel(label_text)
        label.setFont(Fonts.BODY)
        if required:
            label.setText(f"{label_text} *")
            label.setStyleSheet(f"color: {Colors.DANGER};")
        layout.addWidget(label)

        # Input widget
        layout.addWidget(input_widget)
        layout.setStretchFactor(input_widget, 1)

        self.setLayout(layout)
        self.input_widget = input_widget

    def value(self):
        """Get the value from the input widget."""
        if isinstance(self.input_widget, QLineEdit):
            return self.input_widget.text()
        elif isinstance(self.input_widget, (QSpinBox, QDoubleSpinBox)):
            return self.input_widget.value()
        elif isinstance(self.input_widget, QComboBox):
            return self.input_widget.currentText()
        return None

    def set_value(self, value):
        """Set the value of the input widget."""
        if isinstance(self.input_widget, QLineEdit):
            self.input_widget.setText(str(value))
        elif isinstance(self.input_widget, (QSpinBox, QDoubleSpinBox)):
            self.input_widget.setValue(float(value))
        elif isinstance(self.input_widget, QComboBox):
            index = self.input_widget.findText(str(value))
            if index >= 0:
                self.input_widget.setCurrentIndex(index)


class StyledButton(QPushButton):
    """A styled button with predefined styles."""

    def __init__(self, text: str, style: str = "primary", parent=None):
        super().__init__(text, parent)
        self.setFont(Fonts.BODY_BOLD)
        self.setFixedHeight(Dimensions.BUTTON_HEIGHT)
        self.setCursor(Qt.PointingHandCursor)

        if style == "primary":
            self.setStyleSheet(Styles.button_primary())
        elif style == "success":
            self.setStyleSheet(Styles.button_success())
        elif style == "danger":
            self.setStyleSheet(Styles.button_danger())
        else:
            self.setStyleSheet(Styles.button_primary())


class StyledTable(QTableWidget):
    """A styled table widget with improved appearance."""

    def __init__(self, columns: list, parent=None):
        super().__init__(parent)
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        self.setStyleSheet(Styles.table())

        # Configure header
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setFont(Fonts.BODY_BOLD)

        # Configure table
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.verticalHeader().setVisible(False)

    def add_row(self, data: list):
        """Add a row of data to the table."""
        row = self.rowCount()
        self.insertRow(row)
        for col, value in enumerate(data):
            item = QTableWidgetItem(str(value))
            item.setFont(Fonts.BODY)
            self.setItem(row, col, item)

    def clear_table(self):
        """Clear all rows from the table."""
        while self.rowCount() > 0:
            self.removeRow(0)

    def get_selected_row_data(self) -> Optional[list]:
        """Get data from the selected row."""
        current_row = self.currentRow()
        if current_row < 0:
            return None

        data = []
        for col in range(self.columnCount()):
            item = self.item(current_row, col)
            data.append(item.text() if item else "")
        return data


class SearchWidget(QWidget):
    """A search widget with input field and search button."""

    def __init__(self, placeholder: str = "Search...", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(placeholder)
        self.search_input.setStyleSheet(Styles.input_field())
        self.search_input.setFixedHeight(Dimensions.INPUT_HEIGHT)
        layout.addWidget(self.search_input)

        self.search_button = StyledButton("Search", "primary")
        layout.addWidget(self.search_button)

        self.setLayout(layout)

    def text(self) -> str:
        """Get the search text."""
        return self.search_input.text()

    def set_text(self, text: str):
        """Set the search text."""
        self.search_input.setText(text)


class StatusBar(QWidget):
    """A status bar widget for displaying messages and progress."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        self.message_label = QLabel("")
        self.message_label.setFont(Fonts.SMALL)
        layout.addWidget(self.message_label)

        layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setFixedHeight(15)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)
        self.setFixedHeight(25)
        self.setStyleSheet(f"background-color: {Colors.LIGHT}; border-top: 1px solid {Colors.LIGHT_MEDIUM};")

    def show_message(self, message: str, timeout: int = 0):
        """Show a status message."""
        self.message_label.setText(message)
        if timeout > 0:
            QTimer.singleShot(timeout, lambda: self.message_label.setText(""))

    def show_progress(self, visible: bool = True):
        """Show or hide the progress bar."""
        self.progress_bar.setVisible(visible)
        if not visible:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)

    def set_progress(self, value: int, maximum: int = 100):
        """Set progress bar value."""
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(value)


class ConfirmationDialog(QDialog):
    """A confirmation dialog with Yes/No buttons."""

    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 150)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setFont(Fonts.BODY)
        layout.addWidget(message_label)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.no_button = StyledButton("No", "danger")
        self.no_button.clicked.connect(self.reject)
        button_layout.addWidget(self.no_button)

        self.yes_button = StyledButton("Yes", "success")
        self.yes_button.clicked.connect(self.accept)
        self.yes_button.setDefault(True)
        button_layout.addWidget(self.yes_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)


class WorkerThread(QThread):
    """A worker thread for running background tasks."""

    finished = pyqtSignal(object)  # Result signal
    error = pyqtSignal(str)       # Error signal
    progress = pyqtSignal(int)    # Progress signal

    def __init__(self, func: Callable, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        """Execute the function in the background thread."""
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


def show_message(parent, title: str, message: str, icon=QMessageBox.Information):
    """Show a message dialog."""
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setIcon(icon)
    msg_box.setFont(Fonts.BODY)
    msg_box.exec_()


def show_error(parent, message: str):
    """Show an error message dialog."""
    show_message(parent, "Error", message, QMessageBox.Critical)


def show_warning(parent, message: str):
    """Show a warning message dialog."""
    show_message(parent, "Warning", message, QMessageBox.Warning)


def show_success(parent, message: str):
    """Show a success message dialog."""
    show_message(parent, "Success", message, QMessageBox.Information)


def ask_confirmation(parent, message: str) -> bool:
    """Ask for user confirmation."""
    dialog = ConfirmationDialog("Confirm Action", message, parent)
    return dialog.exec_() == QDialog.Accepted


def get_input(parent, title: str, label: str, default: str = "") -> Optional[str]:
    """Get text input from user."""
    text, ok = QInputDialog.getText(parent, title, label, text=default)
    return text if ok else None
