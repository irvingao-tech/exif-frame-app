"""Left Panel — Minimal image list with drag-drop."""

import os
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem,
    QFileDialog, QLabel, QHBoxLayout,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont

SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}


class ImageListPanel(QWidget):
    image_selected = Signal(str)
    images_imported = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumWidth(200)
        self.setMaximumWidth(320)
        self._filepaths: set[str] = set()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(12)

        # ── Header ────────────────────────────────────────────────────
        header = QLabel('图库')
        header.setFont(QFont('SF Pro Display, Segoe UI, PingFang SC', 13))
        header.setStyleSheet('font-weight: 700; color: #1D1D1F; letter-spacing: -0.2px;')
        layout.addWidget(header)

        # ── Import row ────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.import_btn = QPushButton('＋ 导入')
        self.import_btn.setObjectName('primaryButton')
        self.import_btn.clicked.connect(self._on_import)
        btn_row.addWidget(self.import_btn)

        self.folder_btn = QPushButton('📁 文件夹')
        self.folder_btn.clicked.connect(self._on_batch)
        btn_row.addWidget(self.folder_btn)

        layout.addLayout(btn_row)

        # ── Drop hint ─────────────────────────────────────────────────
        self.hint = QLabel('拖拽图片到此处')
        self.hint.setAlignment(Qt.AlignCenter)
        self.hint.setStyleSheet(
            'color: #AEAEB2; font-size: 12px; padding: 24px 16px;'
            'border: 1.5px dashed rgba(60,60,67,0.16); border-radius: 16px;'
        )
        layout.addWidget(self.hint)

        # ── List ──────────────────────────────────────────────────────
        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self._on_selection)
        layout.addWidget(self.list_widget, 1)

        # ── Clear ─────────────────────────────────────────────────────
        self.clear_btn = QPushButton('清空')
        self.clear_btn.clicked.connect(self._on_clear)
        layout.addWidget(self.clear_btn)

    # ── Slots ─────────────────────────────────────────────────────────
    def _on_import(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, '选择图片', '', 'Images (*.jpg *.jpeg *.png *.tiff *.tif)')
        if files:
            self._add_files(files)

    def _on_batch(self):
        folder = QFileDialog.getExistingDirectory(self, '选择文件夹')
        if folder:
            imgs = [os.path.join(folder, f) for f in os.listdir(folder)
                    if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS]
            if imgs:
                self._add_files(imgs)

    def _on_clear(self):
        self.list_widget.clear()
        self._filepaths.clear()
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
            item = QListWidgetItem(os.path.basename(f))
            item.setData(Qt.UserRole, f)
            item.setToolTip(f)
            self.list_widget.addItem(item)
            self._filepaths.add(f)
        if self.list_widget.currentRow() < 0 and self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
        self.images_imported.emit(valid)

    def add_files(self, files: list[str]):
        self._add_files(files)

    def select_last(self):
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(self.list_widget.count() - 1)

    # ── Drag & Drop ───────────────────────────────────────────────────
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(
                'ImageListPanel { border: 2px solid #007AFF; border-radius: 16px; }')

    def dragLeaveEvent(self, event):
        self.setStyleSheet('')

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet('')
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
