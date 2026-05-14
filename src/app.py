"""
Application entry point
Initializes QApplication and shows the main window.
"""

import sys
import logging

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from src.ui.main_window import MainWindow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName('EXIF Frame Card')
    app.setOrganizationName('EXIFFrame')
    
    # Set default font
    font = QFont('Segoe UI', 9)
    app.setFont(font)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    logger.info('Application started')
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
