"""
PharmaPOS ERP - Design Tokens

Modern design system for a premium ERP feel.
Tailored for General Retail and Pharmaceutical businesses in Nigeria.
"""

from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt

class Theme:
    # --- Color Palette (Modern ERP) ---
    # Surfaces
    SURFACE_MAIN = "#F8FAFC"      # Soft light gray background
    SURFACE_CARD = "#FFFFFF"      # Pure white for cards/content
    SURFACE_SIDEBAR = "#0F172A"   # Deep Slate/Indigo for sidebar
    SURFACE_HEADER = "#FFFFFF"
    SURFACE_LIGHT = "#F1F5F9"     # Very light gray for backgrounds
    
    # Primaries (Indigo based for premium feel)
    PRIMARY = "#6366F1"           # Indigo 500
    PRIMARY_HOVER = "#4F46E5"     # Indigo 600
    PRIMARY_LIGHT = "#EEF2FF"     # Indigo 50
    
    # Status Colors (Modern & Accessible)
    SUCCESS = "#10B981"           # Emerald 500 (Pharma feel)
    SUCCESS_LIGHT = "#D1FAE5"
    
    WARNING = "#F59E0B"           # Amber 500
    WARNING_LIGHT = "#FEF3C7"
    
    DANGER = "#EF4444"            # Red 500
    DANGER_LIGHT = "#FEE2E2"
    
    INFO = "#3B82F6"              # Blue 500
    INFO_LIGHT = "#DBEAFE"
    
    # Text
    TEXT_MAIN = "#1E293B"         # Slate 800
    TEXT_MUTED = "#64748B"        # Slate 500
    TEXT_INVERSE = "#FFFFFF"
    
    # Border
    BORDER = "#E2E8F0"            # Slate 200
    BORDER_LIGHT = "#F1F5F9"      # Slate 100

class Typography:
    # Using Segoe UI (standard on Windows) or Inter if available
    FAMILY = "Segoe UI"
    
    H1 = QFont(FAMILY, 24, QFont.Bold)
    H2 = QFont(FAMILY, 18, QFont.Bold)
    H3 = QFont(FAMILY, 14, QFont.Bold)
    
    BODY = QFont(FAMILY, 11)
    BODY_SEMIBOLD = QFont(FAMILY, 11, QFont.DemiBold)
    
    SMALL = QFont(FAMILY, 9)
    CAPTION = QFont(FAMILY, 8)

class Spacing:
    XS = 4
    SM = 8
    MD = 16
    LG = 24
    XL = 32
    
    RADIUS_SM = 4
    RADIUS_MD = 8
    RADIUS_LG = 12
    RADIUS_FULL = 9999
