"""Design system inspired by Material Design 3 + Apple HIG.

Provides consistent colors, typography, spacing, and widget styles
for a modern, professional desktop application.
"""

from PySide6.QtGui import QFont, QColor, QPalette
from PySide6.QtWidgets import QApplication


# ── Color Palette (Material Design 3 + Apple HIG) ──────────────

class Colors:
    """Design tokens for the application color system (light mode)."""

    # Primary (Deep Blue — professional, trustworthy)
    PRIMARY = "#1a73e8"
    PRIMARY_LIGHT = "#4da3ff"
    PRIMARY_DARK = "#004ba0"
    ON_PRIMARY = "#ffffff"

    # Secondary (Teal — complementary, modern)
    SECONDARY = "#00897b"
    SECONDARY_LIGHT = "#4ebaaa"
    SECONDARY_DARK = "#005b4f"
    ON_SECONDARY = "#ffffff"

    # Surface & Background (Apple-inspired subtle grays)
    BACKGROUND = "#f5f5f7"
    SURFACE = "#ffffff"
    SURFACE_VARIANT = "#f0f0f2"
    SURFACE_HOVER = "#e8e8ed"
    ON_BACKGROUND = "#1d1d1f"
    ON_SURFACE = "#1d1d1f"
    ON_SURFACE_VARIANT = "#6e6e73"

    # Status
    SUCCESS = "#34c759"      # Apple green
    WARNING = "#ff9500"      # Apple orange
    ERROR = "#ff3b30"        # Apple red
    INFO = "#007aff"         # Apple blue

    # Borders & Dividers
    OUTLINE = "#d2d2d7"
    OUTLINE_VARIANT = "#e5e5ea"
    DIVIDER = "#e5e5ea"

    # Elevation shadows
    SHADOW_LIGHT = "rgba(0, 0, 0, 0.05)"
    SHADOW_MEDIUM = "rgba(0, 0, 0, 0.1)"
    SHADOW_HEAVY = "rgba(0, 0, 0, 0.15)"


class DarkColors:
    """Design tokens for dark mode."""

    PRIMARY = "#4da3ff"
    PRIMARY_LIGHT = "#80c4ff"
    PRIMARY_DARK = "#1a73e8"
    ON_PRIMARY = "#000000"

    SECONDARY = "#4ebaaa"
    SECONDARY_LIGHT = "#80ddd0"
    SECONDARY_DARK = "#00897b"
    ON_SECONDARY = "#000000"

    BACKGROUND = "#1c1c1e"
    SURFACE = "#2c2c2e"
    SURFACE_VARIANT = "#3a3a3c"
    SURFACE_HOVER = "#48484a"
    ON_BACKGROUND = "#f5f5f7"
    ON_SURFACE = "#f5f5f7"
    ON_SURFACE_VARIANT = "#98989d"

    SUCCESS = "#30d158"
    WARNING = "#ff9f0a"
    ERROR = "#ff453a"
    INFO = "#0a84ff"

    OUTLINE = "#48484a"
    OUTLINE_VARIANT = "#3a3a3c"
    DIVIDER = "#3a3a3c"

    SHADOW_LIGHT = "rgba(0, 0, 0, 0.2)"
    SHADOW_MEDIUM = "rgba(0, 0, 0, 0.3)"
    SHADOW_HEAVY = "rgba(0, 0, 0, 0.4)"


# ── Typography (Apple SF Pro inspired) ──────────────────────────

class Fonts:
    """Typography system."""

    FAMILY = "Segoe UI, SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif"
    FAMILY_MONO = "Cascadia Code, SF Mono, Consolas, monospace"

    @staticmethod
    def body() -> QFont:
        return QFont(Fonts.FAMILY, 12, QFont.Weight.Normal)


# ── Spacing (8px grid system) ──────────────────────────────────

class Spacing:
    """8px grid spacing system."""

    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32
    XXXL = 48


# ── Border Radius (Apple-inspired rounded corners) ─────────────

class Radius:
    """Border radius tokens."""

    SM = 6
    MD = 10
    LG = 14
    XL = 20
    FULL = 999


# ── Stylesheet Builder ─────────────────────────────────────────

def _build_stylesheet(c: type = Colors) -> str:
    """Build the complete application stylesheet.

    Args:
        c: Color class (Colors for light, DarkColors for dark)
    """
    Colors = c  # noqa: shadow for f-string references

    return f"""
    /* ── Global ──────────────────────────────────────────── */
    * {{
        font-family: {Fonts.FAMILY};
        font-size: 12px;
    }}

    /* ── Main Window ─────────────────────────────────────── */
    QMainWindow {{
        background-color: {Colors.BACKGROUND};
    }}

    /* ── Tab Widget ──────────────────────────────────────── */
    QTabWidget::pane {{
        background: {Colors.SURFACE};
        border: 1px solid {Colors.OUTLINE_VARIANT};
        border-radius: {Radius.MD}px;
        margin-top: -1px;
    }}

    QTabBar::tab {{
        background: transparent;
        color: {Colors.ON_SURFACE_VARIANT};
        padding: {Spacing.SM}px {Spacing.LG}px;
        margin-right: {Spacing.XS}px;
        border-bottom: 2px solid transparent;
        font-weight: 500;
        font-size: 13px;
    }}

    QTabBar::tab:hover {{
        color: {Colors.PRIMARY};
        background: {Colors.SURFACE_HOVER};
        border-top-left-radius: {Radius.SM}px;
        border-top-right-radius: {Radius.SM}px;
    }}

    QTabBar::tab:selected {{
        color: {Colors.PRIMARY};
        border-bottom: 2px solid {Colors.PRIMARY};
        font-weight: 600;
    }}

    /* ── Group Box ───────────────────────────────────────── */
    QGroupBox {{
        background: {Colors.SURFACE};
        border: 1px solid {Colors.OUTLINE_VARIANT};
        border-radius: {Radius.MD}px;
        margin-top: {Spacing.SM}px;
        padding-top: {Spacing.LG}px;
        font-weight: 600;
        font-size: 13px;
        color: {Colors.ON_SURFACE};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        left: {Spacing.MD}px;
        padding: 0 {Spacing.SM}px;
        color: {Colors.ON_SURFACE};
    }}

    /* ── Buttons ─────────────────────────────────────────── */
    QPushButton {{
        background: {Colors.SURFACE};
        color: {Colors.ON_SURFACE};
        border: 1px solid {Colors.OUTLINE};
        border-radius: {Radius.SM}px;
        padding: {Spacing.SM}px {Spacing.LG}px;
        font-weight: 500;
        font-size: 12px;
        min-height: 20px;
    }}

    QPushButton:hover {{
        background: {Colors.SURFACE_HOVER};
        border-color: {Colors.PRIMARY_LIGHT};
    }}

    QPushButton:pressed {{
        background: {Colors.OUTLINE_VARIANT};
    }}

    QPushButton:disabled {{
        background: {Colors.SURFACE_VARIANT};
        color: {Colors.ON_SURFACE_VARIANT};
        border-color: {Colors.OUTLINE_VARIANT};
    }}

    /* ── Primary Button ──────────────────────────────────── */
    QPushButton#primaryButton,
    QPushButton[objectName="startButton"] {{
        background: {Colors.PRIMARY};
        color: {Colors.ON_PRIMARY};
        border: none;
        font-weight: 600;
    }}

    QPushButton#primaryButton:hover,
    QPushButton[objectName="startButton"]:hover {{
        background: {Colors.PRIMARY_LIGHT};
    }}

    /* ── Danger Button ───────────────────────────────────── */
    QPushButton#dangerButton {{
        background: {Colors.ERROR};
        color: white;
        border: none;
    }}

    QPushButton#dangerButton:hover {{
        background: #ff6b5b;
    }}

    /* ── Input Fields ────────────────────────────────────── */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background: {Colors.SURFACE};
        color: {Colors.ON_SURFACE};
        border: 1px solid {Colors.OUTLINE};
        border-radius: {Radius.SM}px;
        padding: {Spacing.SM}px {Spacing.MD}px;
        selection-background-color: {Colors.PRIMARY_LIGHT};
        selection-color: white;
    }}

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 2px solid {Colors.PRIMARY};
    }}

    /* ── Spin Box ────────────────────────────────────────── */
    QSpinBox, QDoubleSpinBox {{
        background: {Colors.SURFACE};
        color: {Colors.ON_SURFACE};
        border: 1px solid {Colors.OUTLINE};
        border-radius: {Radius.SM}px;
        padding: {Spacing.SM}px {Spacing.MD}px;
    }}

    QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 2px solid {Colors.PRIMARY};
    }}

    QSpinBox::up-button, QDoubleSpinBox::up-button,
    QSpinBox::down-button, QDoubleSpinBox::down-button {{
        background: {Colors.SURFACE_VARIANT};
        border: none;
        width: 20px;
    }}

    /* ── Combo Box ───────────────────────────────────────── */
    QComboBox {{
        background: {Colors.SURFACE};
        color: {Colors.ON_SURFACE};
        border: 1px solid {Colors.OUTLINE};
        border-radius: {Radius.SM}px;
        padding: {Spacing.SM}px {Spacing.MD}px;
        min-height: 20px;
    }}

    QComboBox:hover {{
        border-color: {Colors.PRIMARY_LIGHT};
    }}

    QComboBox:focus {{
        border: 2px solid {Colors.PRIMARY};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}

    QComboBox QAbstractItemView {{
        background: {Colors.SURFACE};
        color: {Colors.ON_SURFACE};
        border: 1px solid {Colors.OUTLINE};
        border-radius: {Radius.SM}px;
        selection-background-color: {Colors.PRIMARY_LIGHT};
        selection-color: white;
    }}

    /* ── Table ───────────────────────────────────────────── */
    QTableWidget {{
        background: {Colors.SURFACE};
        alternate-background-color: {Colors.SURFACE_VARIANT};
        gridline-color: {Colors.DIVIDER};
        border: 1px solid {Colors.OUTLINE_VARIANT};
        border-radius: {Radius.SM}px;
    }}

    QTableWidget::item {{
        padding: {Spacing.SM}px;
    }}

    QTableWidget::item:selected {{
        background: {Colors.PRIMARY_LIGHT};
        color: white;
    }}

    QHeaderView::section {{
        background: {Colors.SURFACE_VARIANT};
        color: {Colors.ON_SURFACE};
        border: none;
        border-bottom: 1px solid {Colors.OUTLINE};
        padding: {Spacing.SM}px {Spacing.MD}px;
        font-weight: 600;
        font-size: 11px;
    }}

    /* ── Progress Bar ────────────────────────────────────── */
    QProgressBar {{
        background: {Colors.SURFACE_VARIANT};
        border: none;
        border-radius: {Radius.SM}px;
        height: 8px;
        text-align: center;
        font-size: 0px;
    }}

    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {Colors.PRIMARY}, stop:1 {Colors.PRIMARY_LIGHT});
        border-radius: {Radius.SM}px;
    }}

    /* ── Scroll Bar ──────────────────────────────────────── */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background: {Colors.OUTLINE};
        border-radius: 4px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {Colors.ON_SURFACE_VARIANT};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        margin: 0;
    }}

    QScrollBar::handle:horizontal {{
        background: {Colors.OUTLINE};
        border-radius: 4px;
        min-width: 30px;
    }}

    /* ── Status Bar ──────────────────────────────────────── */
    QStatusBar {{
        background: {Colors.SURFACE};
        color: {Colors.ON_SURFACE_VARIANT};
        border-top: 1px solid {Colors.OUTLINE_VARIANT};
        font-size: 11px;
    }}

    /* ── Menu Bar ────────────────────────────────────────── */
    QMenuBar {{
        background: {Colors.SURFACE};
        color: {Colors.ON_SURFACE};
        border-bottom: 1px solid {Colors.OUTLINE_VARIANT};
        padding: {Spacing.XS}px;
    }}

    QMenuBar::item:selected {{
        background: {Colors.SURFACE_HOVER};
        border-radius: {Radius.SM}px;
    }}

    QMenu {{
        background: {Colors.SURFACE};
        color: {Colors.ON_SURFACE};
        border: 1px solid {Colors.OUTLINE};
        border-radius: {Radius.MD}px;
        padding: {Spacing.SM}px;
    }}

    QMenu::item {{
        padding: {Spacing.SM}px {Spacing.XL}px {Spacing.SM}px {Spacing.LG}px;
        border-radius: {Radius.SM}px;
    }}

    QMenu::item:selected {{
        background: {Colors.PRIMARY};
        color: {Colors.ON_PRIMARY};
    }}

    QMenu::separator {{
        height: 1px;
        background: {Colors.DIVIDER};
        margin: {Spacing.SM}px {Spacing.MD}px;
    }}

    /* ── Toolbar ─────────────────────────────────────────── */
    QToolBar {{
        background: {Colors.SURFACE};
        border-bottom: 1px solid {Colors.OUTLINE_VARIANT};
        padding: {Spacing.SM}px;
        spacing: {Spacing.SM}px;
    }}

    QToolBar QToolButton {{
        background: transparent;
        border: none;
        border-radius: {Radius.SM}px;
        padding: {Spacing.SM}px {Spacing.MD}px;
        color: {Colors.ON_SURFACE};
        font-weight: 500;
    }}

    QToolBar QToolButton:hover {{
        background: {Colors.SURFACE_HOVER};
    }}

    /* ── Tooltips ────────────────────────────────────────── */
    QToolTip {{
        background: {Colors.ON_SURFACE};
        color: {Colors.SURFACE};
        border: none;
        border-radius: {Radius.SM}px;
        padding: {Spacing.SM}px {Spacing.MD}px;
        font-size: 11px;
    }}

    /* ── Labels ──────────────────────────────────────────── */
    QLabel {{
        color: {Colors.ON_SURFACE};
    }}

    QLabel#statusIdle {{
        color: {Colors.ON_SURFACE_VARIANT};
    }}

    QLabel#statusRunning {{
        color: {Colors.SUCCESS};
        font-weight: 600;
    }}

    QLabel#statusWarning {{
        color: {Colors.WARNING};
        font-weight: 600;
    }}

    QLabel#statusError {{
        color: {Colors.ERROR};
        font-weight: 600;
    }}

    /* ── Splitter ────────────────────────────────────────── */
    QSplitter::handle {{
        background: {Colors.OUTLINE_VARIANT};
    }}

    QSplitter::handle:horizontal {{
        width: 4px;
    }}

    QSplitter::handle:vertical {{
        height: 4px;
    }}

    /* ── Check Box ───────────────────────────────────────── */
    QCheckBox {{
        spacing: {Spacing.SM}px;
        color: {Colors.ON_SURFACE};
    }}

    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {Colors.OUTLINE};
        border-radius: 4px;
        background: {Colors.SURFACE};
    }}

    QCheckBox::indicator:checked {{
        background: {Colors.PRIMARY};
        border-color: {Colors.PRIMARY};
    }}

    /* ── Radio Button ────────────────────────────────────── */
    QRadioButton {{
        spacing: {Spacing.SM}px;
        color: {Colors.ON_SURFACE};
    }}

    QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {Colors.OUTLINE};
        border-radius: 9px;
        background: {Colors.SURFACE};
    }}

    QRadioButton::indicator:checked {{
        background: {Colors.PRIMARY};
        border-color: {Colors.PRIMARY};
    }}
    """


def apply_theme(app: QApplication, dark_mode: bool | None = None) -> None:
    """Apply the design system to the application.

    Args:
        app: QApplication instance
        dark_mode: True=dark, False=light, None=auto-detect from system
    """
    if dark_mode is None:
        # Detect system dark mode
        palette = app.palette()
        bg = palette.color(QPalette.ColorRole.Window)
        dark_mode = bg.lightness() < 128

    c = DarkColors if dark_mode else Colors
    app.setStyleSheet(_build_stylesheet(c))

    # Set default font
    font = Fonts.body()
    app.setFont(font)

    # Set palette for non-stylesheet elements
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(c.BACKGROUND))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(c.ON_BACKGROUND))
    palette.setColor(QPalette.ColorRole.Base, QColor(c.SURFACE))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(c.SURFACE_VARIANT))
    palette.setColor(QPalette.ColorRole.Text, QColor(c.ON_SURFACE))
    palette.setColor(QPalette.ColorRole.Button, QColor(c.SURFACE))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(c.ON_SURFACE))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(c.PRIMARY))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(c.ON_PRIMARY))
    app.setPalette(palette)
