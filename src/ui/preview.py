"""Center preview panel."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QHBoxLayout,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QEvent, QPoint
from PySide6.QtGui import QPixmap, QImage

from PIL import Image


class PreviewPanel(QWidget):
    export_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('PreviewPanel')
        self._current_preview: Image.Image | None = None
        self._zoom_factor = 1.0
        self._dragging = False
        self._drag_start = QPoint()
        self._drag_h_start = 0
        self._drag_v_start = 0
        self._source_pixmap: QPixmap | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel('Preview')
        title.setObjectName('PreviewTitle')
        header.addWidget(title)
        header.addStretch()

        self.export_btn = QPushButton('Export')
        self.export_btn.setObjectName('primaryButton')
        self.export_btn.clicked.connect(self.export_requested.emit)
        header.addWidget(self.export_btn)
        layout.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setObjectName('PreviewCanvas')
        self.scroll.setWidgetResizable(False)
        self.scroll.setAlignment(Qt.AlignCenter)
        self.scroll.setStyleSheet(
            'QScrollArea#PreviewCanvas { background: #F7F7F8; '
            'border: 1px solid #E4E4E7; border-radius: 14px; }'
        )

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(360, 360)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setText('Import a photo to start')
        self.image_label.installEventFilter(self)
        self.scroll.viewport().installEventFilter(self)
        self.image_label.setStyleSheet(
            'QLabel { background: transparent; color: #8E8E93; font-size: 14px; }'
        )

        self.scroll.setWidget(self.image_label)
        layout.addWidget(self.scroll, 1)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel and self._current_preview is not None:
            self._zoom_from_wheel(event, obj)
            return True
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            return self._start_pan(event)
        if event.type() == QEvent.MouseMove and self._dragging:
            return self._pan(event)
        if event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            return self._end_pan()
        return super().eventFilter(obj, event)

    def set_preview(self, pil_image: Image.Image | None):
        if pil_image is None:
            self.image_label.setPixmap(QPixmap())
            self.image_label.setText('Preview unavailable')
            self._current_preview = None
            self._source_pixmap = None
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
        self._source_pixmap = QPixmap.fromImage(qimg.copy())
        self._render_preview()

    def reset_view(self):
        self._zoom_factor = 1.0
        self._dragging = False
        if self._current_preview:
            self._render_preview()

    def _render_preview(self, anchor=None, old_scale=None):
        if self._source_pixmap is None or self._source_pixmap.isNull():
            return

        viewport = self.scroll.viewport().size()
        available_w = max(viewport.width() - 44, 1)
        available_h = max(viewport.height() - 44, 1)
        fit_scale = min(
            available_w / self._source_pixmap.width(),
            available_h / self._source_pixmap.height(),
        )
        scale = max(fit_scale * self._zoom_factor, 0.05)
        w = max(int(self._source_pixmap.width() * scale), 1)
        h = max(int(self._source_pixmap.height() * scale), 1)
        transform = Qt.SmoothTransformation if scale < 1.8 else Qt.FastTransformation
        pixmap = self._source_pixmap.scaled(w, h, Qt.KeepAspectRatio, transform)

        self.image_label.setText('')
        self.image_label.setPixmap(pixmap)
        self.image_label.resize(max(w, available_w), max(h, available_h))

        if anchor is not None and old_scale:
            self._keep_anchor_visible(anchor, old_scale, scale)

    def _zoom_from_wheel(self, event, obj):
        delta = event.angleDelta().y()
        if delta == 0:
            return

        old_scale = self._current_effective_scale()
        viewport_pos = event.position().toPoint()
        if obj is self.image_label:
            viewport_pos = self.scroll.viewport().mapFromGlobal(
                self.image_label.mapToGlobal(viewport_pos)
            )

        hbar = self.scroll.horizontalScrollBar()
        vbar = self.scroll.verticalScrollBar()
        anchor = (hbar.value() + viewport_pos.x(), vbar.value() + viewport_pos.y())

        step = 1.12 if delta > 0 else 1 / 1.12
        self._zoom_factor = min(max(self._zoom_factor * step, 0.35), 8.0)
        self._render_preview(anchor=anchor, old_scale=old_scale)

    def _start_pan(self, event) -> bool:
        if self._current_preview is None:
            return False
        self._dragging = True
        self._drag_start = event.globalPosition().toPoint()
        self._drag_h_start = self.scroll.horizontalScrollBar().value()
        self._drag_v_start = self.scroll.verticalScrollBar().value()
        self.scroll.viewport().setCursor(Qt.ClosedHandCursor)
        self.image_label.setCursor(Qt.ClosedHandCursor)
        return True

    def _pan(self, event) -> bool:
        delta = event.globalPosition().toPoint() - self._drag_start
        self.scroll.horizontalScrollBar().setValue(self._drag_h_start - delta.x())
        self.scroll.verticalScrollBar().setValue(self._drag_v_start - delta.y())
        return True

    def _end_pan(self) -> bool:
        self._dragging = False
        self.scroll.viewport().setCursor(Qt.ArrowCursor)
        self.image_label.setCursor(Qt.ArrowCursor)
        return True

    def _current_effective_scale(self) -> float:
        if self._current_preview is None:
            return 1.0
        viewport = self.scroll.viewport().size()
        fit_scale = min(
            max(viewport.width() - 44, 1) / self._current_preview.width,
            max(viewport.height() - 44, 1) / self._current_preview.height,
        )
        return max(fit_scale * self._zoom_factor, 0.05)

    def _keep_anchor_visible(self, anchor, old_scale: float, new_scale: float):
        ratio = new_scale / old_scale
        cursor = self.scroll.viewport().mapFromGlobal(self.cursor().pos())
        hbar = self.scroll.horizontalScrollBar()
        vbar = self.scroll.verticalScrollBar()
        hbar.setValue(int(anchor[0] * ratio - cursor.x()))
        vbar.setValue(int(anchor[1] * ratio - cursor.y()))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._current_preview:
            self._render_preview()

    def get_current_preview(self) -> Image.Image | None:
        return self._current_preview
