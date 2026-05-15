"""Center Panel — Liquid Glass preview area."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QHBoxLayout,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage, QFont

from PIL import Image


class PreviewPanel(QWidget):
    export_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_preview: Image.Image | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(12)

        # ── Title ─────────────────────────────────────────────────────
        title = QLabel('预览')
        title.setFont(QFont('SF Pro Display, Segoe UI, PingFang SC', 12))
        title.setStyleSheet('font-weight: 600; color: #6E6E73;')
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # ── Preview canvas ────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            'QScrollArea {'
            '  background: #E8E8ED;'
            '  border: 1px solid rgba(60,60,67,0.10);'
            '  border-radius: 20px;'
            '}'
        )

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(300, 300)
        self.image_label.setStyleSheet(
            'QLabel {'
            '  background: #E8E8ED;'
            '  border-radius: 20px;'
            '  color: #AEAEB2;'
            '  font-size: 14px;'
            '}'
        )
        self.image_label.setText('导入图片以查看预览')

        scroll.setWidget(self.image_label)
        layout.addWidget(scroll, 1)

        # ── Export button ─────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.export_btn = QPushButton('导出图片')
        self.export_btn.setObjectName('primaryButton')
        self.export_btn.clicked.connect(self.export_requested.emit)
        btn_row.addWidget(self.export_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

    def set_preview(self, pil_image: Image.Image | None):
        if pil_image is None:
            self.image_label.setText('无法生成预览')
            self.image_label.setStyleSheet(
                'QLabel { background: #E8E8ED; border-radius: 20px; color: #AEAEB2; font-size: 14px; }')
            return

        self._current_preview = pil_image

        if pil_image.mode == 'RGB':
            qimg = QImage(pil_image.tobytes('raw', 'RGB'),
                          pil_image.width, pil_image.height,
                          pil_image.width * 3, QImage.Format_RGB888)
        elif pil_image.mode == 'RGBA':
            qimg = QImage(pil_image.tobytes('raw', 'RGBA'),
                          pil_image.width, pil_image.height,
                          pil_image.width * 4, QImage.Format_RGBA8888)
        else:
            rgb = pil_image.convert('RGB')
            qimg = QImage(rgb.tobytes('raw', 'RGB'),
                          rgb.width, rgb.height,
                          rgb.width * 3, QImage.Format_RGB888)

        scale = min(
            (self.image_label.width() - 40) / qimg.width(),
            (self.image_label.height() - 40) / qimg.height(),
            1.0
        )
        if scale < 1.0:
            w = int(qimg.width() * scale)
            h = int(qimg.height() * scale)
            pixmap = QPixmap.fromImage(qimg).scaled(
                w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            pixmap = QPixmap.fromImage(qimg)

        self.image_label.setPixmap(pixmap)
        self.image_label.setStyleSheet(
            'QLabel { background: #E8E8ED; border-radius: 20px; }')

    def resizeEvent(self, event):
        """Re-scale preview when panel is resized."""
        super().resizeEvent(event)
        if self._current_preview:
            self.set_preview(self._current_preview)
    
    def get_current_preview(self) -> Image.Image | None:
        return self._current_preview
