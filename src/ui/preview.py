"""
Center Panel: Preview Area
Shows the rendered preview image, updates in real-time.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QHBoxLayout,
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap, QImage, QFont

from PIL import Image


class PreviewPanel(QWidget):
    """Center panel: large preview of the rendered frame."""
    
    export_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_preview: Image.Image | None = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(4)
        
        # Title
        title = QLabel('预览')
        title.setFont(QFont('Segoe UI', 11, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Scroll area for preview
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; background: #111113; border-radius: 16px; }')
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(300, 300)
        self.image_label.setStyleSheet('background: #111113; border-radius: 16px;')
        self.image_label.setText('导入图片以查看预览')
        self.image_label.setFont(QFont('Segoe UI', 13))
        self.image_label.setStyleSheet(
            'QLabel { color: #8E8E93; background: #111113; border-radius: 16px; }'
        )
        
        scroll.setWidget(self.image_label)
        layout.addWidget(scroll, 1)
        
        # Export button
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        
        self.export_btn = QPushButton('导出图片')
        self.export_btn.setObjectName('primaryButton')
        self.export_btn.setStyleSheet("")
        self.export_btn.clicked.connect(self.export_requested.emit)
        export_layout.addWidget(self.export_btn)
        
        export_layout.addStretch()
        layout.addLayout(export_layout)
    
    def set_preview(self, pil_image: Image.Image | None):
        """Display a PIL Image as preview."""
        if pil_image is None:
            self.image_label.setText('无法生成预览')
            self.image_label.setStyleSheet(
                'QLabel { color: #8E8E93; background: #111113; border-radius: 16px; }'
            )
            return
        
        self._current_preview = pil_image
        
        # Convert PIL to QPixmap
        if pil_image.mode == 'RGB':
            qimg = QImage(
                pil_image.tobytes('raw', 'RGB'),
                pil_image.width, pil_image.height,
                pil_image.width * 3,
                QImage.Format_RGB888
            )
        elif pil_image.mode == 'RGBA':
            qimg = QImage(
                pil_image.tobytes('raw', 'RGBA'),
                pil_image.width, pil_image.height,
                pil_image.width * 4,
                QImage.Format_RGBA8888
            )
        else:
            rgb = pil_image.convert('RGB')
            qimg = QImage(
                rgb.tobytes('raw', 'RGB'),
                rgb.width, rgb.height,
                rgb.width * 3,
                QImage.Format_RGB888
            )
        
        pixmap = QPixmap.fromImage(qimg)
        
        # Scale to fit while maintaining aspect ratio
        available = self.image_label.size()
        if available.width() > 50 and available.height() > 50:
            scaled = pixmap.scaled(
                available.width() - 20,
                available.height() - 20,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        else:
            scaled = pixmap
        
        self.image_label.setPixmap(scaled)
        self.image_label.setStyleSheet('background: #111113; border-radius: 16px;')
    
    def resizeEvent(self, event):
        """Re-scale preview when panel is resized."""
        super().resizeEvent(event)
        if self._current_preview:
            self.set_preview(self._current_preview)
    
    def get_current_preview(self) -> Image.Image | None:
        return self._current_preview
