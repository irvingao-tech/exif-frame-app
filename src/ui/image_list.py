"""Left panel image list."""

import os
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem,
    QFileDialog, QLabel, QHBoxLayout,
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import (
    QDragEnterEvent, QDropEvent, QImageReader, QPixmap, QPainter,
    QColor,
)

from src.core.local_cache import thumbnail_cache_path

SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}
THUMBNAIL_SIZE = 54


def make_thumbnail(filepath: str, size: int = THUMBNAIL_SIZE) -> QPixmap:
    """Create a small square thumbnail without loading more pixels than needed."""
    cache_path = thumbnail_cache_path(filepath, size)
    if cache_path.exists():
        cached = QPixmap(str(cache_path))
        if not cached.isNull():
            return cached

    reader = QImageReader(filepath)
    reader.setAutoTransform(True)
    original = reader.size()
    if original.isValid() and original.width() > 0 and original.height() > 0:
        scale = max(size / original.width(), size / original.height())
        reader.setScaledSize(QSize(
            max(size, int(original.width() * scale)),
            max(size, int(original.height() * scale)),
        ))
    image = reader.read()

    canvas = QPixmap(size, size)
    canvas.fill(Qt.transparent)

    if not image.isNull():
        pix = QPixmap.fromImage(image).scaled(
            size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
        )
        x = (size - pix.width()) // 2
        y = (size - pix.height()) // 2
        painter = QPainter(canvas)
        painter.drawPixmap(x, y, pix)
        painter.end()
    else:
        canvas.fill(QColor('#E4E4E7'))
    try:
        canvas.save(str(cache_path), 'PNG')
    except Exception:
        pass
    return canvas


class PhotoListRow(QWidget):
    """Compact thumbnail row used in the left photo list."""

    def __init__(self, filepath: str, parent=None):
        super().__init__(parent)
        self.filepath = filepath
        self.setObjectName('PhotoListRow')
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 5, 8, 5)
        layout.setSpacing(10)

        self.thumb = QLabel()
        self.thumb.setObjectName('PhotoThumb')
        self.thumb.setFixedSize(THUMBNAIL_SIZE, THUMBNAIL_SIZE)
        placeholder = QPixmap(THUMBNAIL_SIZE, THUMBNAIL_SIZE)
        placeholder.fill(QColor('#EDEDEF'))
        self.thumb.setPixmap(placeholder)
        layout.addWidget(self.thumb)

        name = QLabel(os.path.basename(filepath))
        name.setObjectName('PhotoName')
        name.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        name.setWordWrap(False)
        layout.addWidget(name, 1)

    def load_thumbnail(self):
        self.thumb.setPixmap(make_thumbnail(self.filepath))


class ImageListPanel(QWidget):
    image_selected = Signal(str)
    images_imported = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('ImageListPanel')
        self.setAcceptDrops(True)
        self.setMinimumWidth(250)
        self.setMaximumWidth(330)
        self._filepaths: set[str] = set()
        self._thumb_queue: list[PhotoListRow] = []
        self._thumb_timer = QTimer(self)
        self._thumb_timer.setInterval(12)
        self._thumb_timer.timeout.connect(self._load_pending_thumbnails)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 10, 14)
        layout.setSpacing(10)

        header = QLabel('Photos')
        header.setObjectName('SidebarTitle')
        layout.addWidget(header)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.import_btn = QPushButton('Import')
        self.import_btn.setObjectName('primaryButton')
        self.import_btn.clicked.connect(self._on_import)
        btn_row.addWidget(self.import_btn)

        self.folder_btn = QPushButton('Folder')
        self.folder_btn.clicked.connect(self._on_batch)
        btn_row.addWidget(self.folder_btn)
        layout.addLayout(btn_row)

        self.hint = QLabel('Drop photos here')
        self.hint.setAlignment(Qt.AlignCenter)
        self.hint.setObjectName('DropHint')
        self.hint.setStyleSheet(
            'QLabel#DropHint { color: #8E8E93; font-size: 12px; padding: 22px 12px; '
            'border: 1px dashed #D4D4D8; border-radius: 12px; background: #FAFAFA; }'
        )
        layout.addWidget(self.hint)

        self.list_widget = QListWidget()
        self.list_widget.setSpacing(3)
        self.list_widget.currentRowChanged.connect(self._on_selection)
        layout.addWidget(self.list_widget, 1)

        self.clear_btn = QPushButton('Clear')
        self.clear_btn.clicked.connect(self._on_clear)
        layout.addWidget(self.clear_btn)

    def _on_import(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, 'Select Photos', '', 'Images (*.jpg *.jpeg *.png *.tiff *.tif)')
        if files:
            self._add_files(files)

    def _on_batch(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder:
            imgs = [os.path.join(folder, f) for f in os.listdir(folder)
                    if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS]
            if imgs:
                self._add_files(imgs)

    def _on_clear(self):
        self.list_widget.clear()
        self._filepaths.clear()
        self._thumb_queue.clear()
        self._thumb_timer.stop()
        self.hint.setVisible(True)

    def _on_selection(self, row: int):
        if row >= 0:
            self.image_selected.emit(self.list_widget.item(row).data(Qt.UserRole))

    def _add_files(self, files: list[str]):
        valid = [f for f in files if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS]
        if not valid:
            return
        self.hint.setVisible(False)
        for f in valid:
            if f in self._filepaths:
                continue
            item = QListWidgetItem()
            item.setData(Qt.UserRole, f)
            item.setToolTip(f)
            item.setSizeHint(QSize(1, THUMBNAIL_SIZE + 12))
            self.list_widget.addItem(item)
            row = PhotoListRow(f)
            self.list_widget.setItemWidget(item, row)
            self._thumb_queue.append(row)
            self._filepaths.add(f)
        if self.list_widget.currentRow() < 0 and self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
        if self._thumb_queue and not self._thumb_timer.isActive():
            self._thumb_timer.start()
        self.images_imported.emit(valid)

    def _load_pending_thumbnails(self):
        for _ in range(3):
            if not self._thumb_queue:
                self._thumb_timer.stop()
                return
            self._thumb_queue.pop(0).load_thumbnail()

    def add_files(self, files: list[str]):
        self._add_files(files)

    def select_last(self):
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(self.list_widget.count() - 1)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.hint.setStyleSheet(
                'QLabel#DropHint { color: #18181B; font-size: 12px; padding: 22px 12px; '
                'border: 1px solid #A1A1AA; border-radius: 12px; background: #FFFFFF; }'
            )

    def dragLeaveEvent(self, event):
        self.hint.setStyleSheet(
            'QLabel#DropHint { color: #8E8E93; font-size: 12px; padding: 22px 12px; '
            'border: 1px dashed #D4D4D8; border-radius: 12px; background: #FAFAFA; }'
        )

    def dropEvent(self, event: QDropEvent):
        self.dragLeaveEvent(event)
        files = [url.toLocalFile() for url in event.mimeData().urls()
                 if os.path.splitext(url.toLocalFile())[1].lower() in SUPPORTED_EXTENSIONS]
        if files:
            self._add_files(files)

    def get_current_filepath(self) -> Optional[str]:
        item = self.list_widget.currentItem()
        return item.data(Qt.UserRole) if item else None

    def get_all_filepaths(self) -> list[str]:
        return [self.list_widget.item(i).data(Qt.UserRole)
                for i in range(self.list_widget.count())]
