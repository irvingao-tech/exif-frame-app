"""
Left Panel: Image List
Shows imported images, supports drag-drop and file selection.
"""

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
    """Left panel: image file list with import buttons."""
    
    image_selected = Signal(str)  # filepath of selected image
    images_imported = Signal(list)  # list of filepaths
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumWidth(200)
        self.setMaximumWidth(320)
        self._filepaths = set()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # Title
        title = QLabel('图片列表')
        title.setFont(QFont('Segoe UI', 11, QFont.Bold))
        layout.addWidget(title)
        
        # Import buttons
        btn_layout = QHBoxLayout()
        
        self.import_btn = QPushButton('导入图片')
        self.import_btn.setObjectName('primaryButton')
        self.import_btn.setStyleSheet("")
        self.import_btn.clicked.connect(self._on_import_clicked)
        btn_layout.addWidget(self.import_btn)
        
        self.batch_btn = QPushButton('批量导入')
        self.batch_btn.setStyleSheet("")
        self.batch_btn.clicked.connect(self._on_batch_clicked)
        btn_layout.addWidget(self.batch_btn)
        
        layout.addLayout(btn_layout)
        
        # Hint label
        self.hint = QLabel('拖拽图片到此处\n或点击按钮选择')
        self.hint.setAlignment(Qt.AlignCenter)
        self.hint.setStyleSheet('color: #8E8E93; font-size: 11px; padding: 16px;')
        layout.addWidget(self.hint)
        
        # Image list
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("")
        self.list_widget.currentRowChanged.connect(self._on_selection_changed)
        layout.addWidget(self.list_widget)
        
        # Clear button
        self.clear_btn = QPushButton('清空列表')
        self.clear_btn.setStyleSheet("")
        self.clear_btn.clicked.connect(self._on_clear)
        layout.addWidget(self.clear_btn)
    
    def _on_import_clicked(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, '选择图片', '',
            'Images (*.jpg *.jpeg *.png *.tiff *.tif)'
        )
        if files:
            self._add_files(files)
    
    def _on_batch_clicked(self):
        folder = QFileDialog.getExistingDirectory(self, '选择文件夹')
        if folder:
            image_files = []
            for f in os.listdir(folder):
                ext = os.path.splitext(f)[1].lower()
                if ext in SUPPORTED_EXTENSIONS:
                    image_files.append(os.path.join(folder, f))
            if image_files:
                self._add_files(image_files)
    
    def _on_clear(self):
        self.list_widget.clear()
        self._filepaths.clear()
        self.hint.setVisible(True)
    
    def _on_selection_changed(self, row: int):
        if row >= 0:
            item = self.list_widget.item(row)
            filepath = item.data(Qt.UserRole)
            self.image_selected.emit(filepath)
    
    def _add_files(self, files: list):
        valid = [f for f in files if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS]
        if not valid:
            return
        
        self.hint.setVisible(False)
        
        for f in valid:
            # Check if already in list
            if f in self._filepaths:
                continue
            
            item = QListWidgetItem(os.path.basename(f))
            item.setData(Qt.UserRole, f)
            item.setToolTip(f)
            self.list_widget.addItem(item)
            self._filepaths.add(f)
        
        # Select first item if nothing selected
        if self.list_widget.currentRow() < 0 and self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
        
        self.images_imported.emit(valid)

    def add_files(self, files: list):
        """Add image files from outside the panel, such as window-level drops."""
        self._add_files(files)
    
    # --- Drag & Drop ---
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet('ImageListPanel { border: 1px solid #0A84FF; border-radius: 14px; }')
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet('')
    
    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet('')
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            ext = os.path.splitext(path)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                files.append(path)
        if files:
            self._add_files(files)
    
    def get_current_filepath(self) -> Optional[str]:
        """Get currently selected image filepath."""
        item = self.list_widget.currentItem()
        if item:
            return item.data(Qt.UserRole)
        return None
    
    def get_all_filepaths(self) -> list:
        """Get all image filepaths in the list."""
        paths = []
        for i in range(self.list_widget.count()):
            paths.append(self.list_widget.item(i).data(Qt.UserRole))
        return paths
