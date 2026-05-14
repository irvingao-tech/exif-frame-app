"""Apple Liquid Glass — EXIF Frame Card. Entry point and global theme."""

import sys
import logging

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QPalette, QColor

from src.ui.main_window import MainWindow

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)

# ── Apple Liquid Glass palette ──────────────────────────────────────────
PALETTE = {
    'glass_bg':       'rgba(255,255,255,0.58)',
    'glass_bg_dark':  'rgba(28,28,30,0.72)',
    'glass_bg_card':  'rgba(255,255,255,0.46)',
    'glass_bg_field': 'rgba(118,118,128,0.12)',
    'panel_fill':     '#F5F5F7',
    'canvas_fill':    '#E8E8ED',
    'text_primary':   '#1D1D1F',
    'text_secondary': '#6E6E73',
    'text_tertiary':  '#AEAEB2',
    'text_white':     '#FFFFFF',
    'accent':         '#007AFF',
    'accent_hover':   '#0062CC',
    'separator':      'rgba(60,60,67,0.12)',
}

# ── Global stylesheet ────────────────────────────────────────────────────
GLOBAL_QSS = f"""
QMainWindow {{
    background: {PALETTE['panel_fill']};
}}
QWidget {{
    font-family: "SF Pro Display","Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
    font-size: 13px;
    color: {PALETTE['text_primary']};
}}
QGroupBox {{
    background: {PALETTE['glass_bg_card']};
    border: 1px solid {PALETTE['separator']};
    border-radius: 14px;
    margin-top: 14px;
    padding: 16px 12px 12px 12px;
    font-weight: 600;
    font-size: 12px;
    color: {PALETTE['text_secondary']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    color: {PALETTE['text_secondary']};
}}
QPushButton {{
    background: {PALETTE['glass_bg']};
    border: 1px solid {PALETTE['separator']};
    border-radius: 10px;
    padding: 7px 18px;
    color: {PALETTE['text_primary']};
    font-weight: 500;
    font-size: 12px;
}}
QPushButton:hover {{
    background: rgba(255,255,255,0.82);
    border-color: rgba(60,60,67,0.24);
}}
QPushButton:pressed {{
    background: rgba(0,0,0,0.06);
}}
QPushButton#primaryButton {{
    background: {PALETTE['accent']};
    color: {PALETTE['text_white']};
    border: none;
    font-weight: 600;
    font-size: 13px;
    padding: 8px 22px;
}}
QPushButton#primaryButton:hover {{
    background: {PALETTE['accent_hover']};
}}
QPushButton#primaryButton:pressed {{
    background: #0055B3;
}}
QLineEdit {{
    background: {PALETTE['glass_bg_field']};
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 6px 10px;
    color: {PALETTE['text_primary']};
    font-size: 12px;
}}
QLineEdit:focus {{
    border-color: {PALETTE['accent']};
    background: {PALETTE['glass_bg']};
}}
QComboBox {{
    background: {PALETTE['glass_bg_field']};
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 5px 10px;
    font-size: 12px;
    color: {PALETTE['text_primary']};
}}
QComboBox:hover {{
    background: {PALETTE['glass_bg']};
}}
QComboBox:focus {{
    border-color: {PALETTE['accent']};
}}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{
    background: #FFFFFF;
    border: 1px solid {PALETTE['separator']};
    border-radius: 10px;
    padding: 4px;
    selection-background-color: {PALETTE['accent']};
    outline: none;
}}
QSlider::groove:horizontal {{
    background: {PALETTE['separator']};
    height: 4px;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: #FFFFFF;
    border: 1.5px solid {PALETTE['separator']};
    width: 18px; height: 18px;
    margin: -7px 0;
    border-radius: 9px;
}}
QSlider::handle:horizontal:hover {{ border-color: {PALETTE['accent']}; }}
QSlider::sub-page:horizontal {{
    background: {PALETTE['accent']};
    border-radius: 2px;
}}
QCheckBox {{
    spacing: 8px;
    font-size: 12px;
    color: {PALETTE['text_secondary']};
}}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border-radius: 5px;
    border: 1.5px solid {PALETTE['separator']};
    background: {PALETTE['glass_bg_field']};
}}
QCheckBox::indicator:checked {{
    background: {PALETTE['accent']};
    border-color: {PALETTE['accent']};
}}
QListWidget {{
    background: {PALETTE['glass_bg_card']};
    border: 1px solid {PALETTE['separator']};
    border-radius: 14px;
    padding: 6px;
    outline: none;
    font-size: 12px;
}}
QListWidget::item {{
    border-radius: 8px;
    padding: 8px 10px;
    margin: 1px 0;
    color: {PALETTE['text_primary']};
}}
QListWidget::item:selected {{
    background: {PALETTE['accent']};
    color: #FFFFFF;
}}
QListWidget::item:hover:!selected {{
    background: rgba(0,122,255,0.10);
}}
QScrollArea {{ background: transparent; border: none; }}
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 4px 0;
}}
QScrollBar::handle:vertical {{
    background: rgba(60,60,67,0.20);
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: rgba(60,60,67,0.36); }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
    margin: 0 4px;
}}
QScrollBar::handle:horizontal {{
    background: rgba(60,60,67,0.20);
    border-radius: 3px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{ background: rgba(60,60,67,0.36); }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QSplitter::handle {{
    background: {PALETTE['separator']};
    width: 1px;
}}
QStatusBar {{
    background: {PALETTE['glass_bg_dark']};
    border-top: 0.5px solid {PALETTE['separator']};
    color: {PALETTE['text_secondary']};
    font-size: 11px;
    padding: 2px 16px;
}}
QToolTip {{
    background: {PALETTE['glass_bg_dark']};
    color: #FFFFFF;
    border: 0.5px solid rgba(255,255,255,0.18);
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 11px;
}}
QPushButton#colorSwatch {{
    border-radius: 10px;
    border: 1.5px solid rgba(0,0,0,0.12);
    min-width: 28px; max-width: 28px;
    min-height: 28px; max-height: 28px;
    padding: 0;
}}
"""


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('EXIF Frame Card')
    app.setOrganizationName('EXIFFrame')

    app.setStyle('Fusion')
    p = app.palette()
    p.setColor(QPalette.Window, QColor('#F5F5F7'))
    app.setPalette(p)

    app.setFont(QFont('SF Pro Display, Segoe UI, PingFang SC', 9))
    app.setStyleSheet(GLOBAL_QSS)

    window = MainWindow()
    window.show()

    logger.info('Application started')
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
