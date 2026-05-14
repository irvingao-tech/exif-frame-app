"""
Main Window
Three-panel layout: Image List | Preview | Controls
Coordinates all interactions between panels.
"""

import os
import logging
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter,
    QMessageBox, QFileDialog, QStatusBar, QApplication,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from src.ui.image_list import ImageListPanel, SUPPORTED_EXTENSIONS
from src.ui.preview import PreviewPanel
from src.ui.controls import ControlsPanel
from src.core.image_processor import process_image, process_preview, RATIOS
from src.core.exporter import export_image, generate_output_filename
from src.templates.base import RenderParams

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle('EXIF Frame Card — 摄影卡片边框')
        self.setMinimumSize(1200, 750)
        self.resize(1400, 850)
        self.setAcceptDrops(True)
        
        # State
        self._current_filepath: Optional[str] = None
        self._rendered_full: Optional[object] = None  # PIL Image at full resolution
        self._exif_cache: dict[str, dict] = {}
        self._preview_cache: dict[tuple, object] = {}
        self._pending_filepath: Optional[str] = None
        self._selection_timer = QTimer()
        self._selection_timer.setSingleShot(True)
        self._selection_timer.setInterval(120)
        self._selection_timer.timeout.connect(self._apply_pending_selection)
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.setInterval(120)  # 120ms debounce
        self._update_timer.timeout.connect(self._update_preview)
        
        self._setup_ui()
        self._connect_signals()
        
        # Apply stylesheet
        self._apply_style()
    
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        
        # Splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Image list
        self.image_list = ImageListPanel()
        splitter.addWidget(self.image_list)
        
        # Center: Preview
        self.preview = PreviewPanel()
        splitter.addWidget(self.preview)
        
        # Right: Controls
        self.controls = ControlsPanel()
        splitter.addWidget(self.controls)
        
        # Set initial sizes
        splitter.setSizes([220, 700, 320])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        
        main_layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setFont(QFont('Segoe UI', 10))
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('就绪 — 拖入图片或点击导入按钮')
    
    def _connect_signals(self):
        # Image list signals
        self.image_list.image_selected.connect(self._on_image_selected)
        
        # Controls signals — debounced preview update
        self.controls.params_changed.connect(self._schedule_preview_update)
        
        # Preview export button
        self.preview.export_requested.connect(self._on_export)
    
    def _on_image_selected(self, filepath: str):
        """Handle image selection from the list."""
        self._pending_filepath = filepath
        self._selection_timer.start()

    def _apply_pending_selection(self):
        """Apply the latest selected image after a short debounce."""
        filepath = self._pending_filepath
        if not filepath or filepath == self._current_filepath:
            return

        self._current_filepath = filepath
        self.status_bar.showMessage(f'已选择: {os.path.basename(filepath)}')
        
        # Read EXIF and populate fields
        exif_data = self._get_exif(filepath)
        self.controls.set_all_exif_fields(exif_data, overwrite=True)
        
        # Update preview
        self._schedule_preview_update()

    def _get_exif(self, filepath: str) -> dict:
        """Read EXIF once per file during the session."""
        if filepath not in self._exif_cache:
            from src.core.exif_reader import read_exif
            self._exif_cache[filepath] = read_exif(filepath)
        return self._exif_cache[filepath]

    def _preview_cache_key(self, filepath: str, params: RenderParams) -> tuple:
        return (
            filepath,
            self.controls.get_template_key(),
            self.controls.get_ratio_key(),
            params.ratio,
            params.bg_color,
            params.margin_top,
            params.margin_side,
            params.margin_bottom,
            params.image_corner_radius,
            params.image_shadow,
            params.font_size,
            params.font_color,
            params.font_bold,
            params.text_align,
            params.logo_enabled,
            params.logo_size,
            params.logo_position,
            params.qr_enabled,
            params.qr_size,
            params.qr_position,
            params.map_provider,
            params.title,
            params.location,
            params.camera,
            params.lens,
            params.focal_length,
            params.aperture,
            params.shutter_speed,
            params.iso,
            params.date,
            params.note,
        )

    def _remember_preview(self, key: tuple, preview_img):
        """Keep a small preview cache for fast back-and-forth browsing."""
        self._preview_cache[key] = preview_img
        if len(self._preview_cache) > 24:
            oldest_key = next(iter(self._preview_cache))
            self._preview_cache.pop(oldest_key, None)
    
    def _schedule_preview_update(self):
        """Debounced preview update."""
        self._update_timer.start()
    
    def _update_preview(self):
        """Render and display the preview."""
        if not self._current_filepath:
            return
        
        try:
            # Build render params from controls
            params = self._build_render_params()
            cache_key = self._preview_cache_key(self._current_filepath, params)
            cached = self._preview_cache.get(cache_key)
            if cached is not None:
                self.preview.set_preview(cached)
                self.status_bar.showMessage(
                    f'预览已更新 — {os.path.basename(self._current_filepath)}'
                )
                return
            
            # Generate preview
            preview_img = process_preview(
                self._current_filepath,
                template_key=self.controls.get_template_key(),
                ratio_key=self.controls.get_ratio_key(),
                render_params=params,
                preview_long_edge=800,
                exif_data=self._get_exif(self._current_filepath),
            )
            
            self._remember_preview(cache_key, preview_img)
            self.preview.set_preview(preview_img)
            self.status_bar.showMessage(
                f'预览已更新 — {os.path.basename(self._current_filepath)}'
            )
        except Exception as e:
            logger.error(f'Preview update error: {e}')
            self.status_bar.showMessage(f'预览错误: {e}')
    
    def _build_render_params(self) -> RenderParams:
        """Build RenderParams from current control values."""
        # Get ratio from controls
        ratio_key = self.controls.get_ratio_key()
        ratio_map = {
            'Original': None,
            '1:1': (1, 1),
            '4:5': (4, 5),
            '3:4': (3, 4),
            '16:9': (16, 9),
            '9:16': (9, 16),
            'A4 Portrait': (210, 297),
            'A4 Landscape': (297, 210),
        }
        ratio = ratio_map.get(ratio_key, (4, 5))
        
        # If Original, get image dimensions
        if ratio is None and self._current_filepath:
            from PIL import Image
            try:
                img = Image.open(self._current_filepath)
                from math import gcd
                g = gcd(img.width, img.height)
                ratio = (img.width // g, img.height // g)
            except Exception:
                ratio = (3, 2)
        
        params = RenderParams(
            ratio=ratio or (3, 2),
            bg_color=self.controls.get_bg_color(),
            margin_top=self.controls.get_margin('margin_top'),
            margin_side=self.controls.get_margin('margin_side'),
            margin_bottom=self.controls.get_margin('margin_bottom'),
            image_corner_radius=self.controls.get_margin('image_corner_radius'),
            image_shadow=self.controls.get_shadow(),
            font_size=self.controls.get_font_size(),
            font_color=self.controls.get_font_color(),
            font_bold=self.controls.get_font_bold(),
            text_align=self.controls.get_text_align(),
            logo_enabled=self.controls.get_logo_enabled(),
            logo_size=self.controls.get_logo_size(),
            logo_position=self.controls.get_logo_position(),
            qr_enabled=self.controls.get_qr_enabled(),
            qr_size=self.controls.get_qr_size(),
            qr_position=self.controls.get_qr_position(),
            map_provider=self.controls.get_map_provider(),
            title=self.controls.get_exif_field('title'),
            location=self.controls.get_exif_field('location'),
            camera=self.controls.get_exif_field('camera'),
            lens=self.controls.get_exif_field('lens'),
            focal_length=self.controls.get_exif_field('focal_length'),
            aperture=self.controls.get_exif_field('aperture'),
            shutter_speed=self.controls.get_exif_field('shutter_speed'),
            iso=self.controls.get_exif_field('iso'),
            date=self.controls.get_exif_field('date'),
            note=self.controls.get_exif_field('note'),
        )
        return params
    
    def _on_export(self):
        """Handle export button click."""
        if not self._current_filepath:
            QMessageBox.warning(self, '提示', '请先导入图片')
            return
        
        # Choose format
        export_format = self.controls.get_export_format()
        ext_filter = 'JPEG (*.jpg);;PNG (*.png)' if export_format == 'JPEG' else 'PNG (*.png);;JPEG (*.jpg)'
        
        # Suggest output filename
        default_name = generate_output_filename(
            self._current_filepath, '_framed',
            '.jpg' if export_format == 'JPEG' else '.png'
        )
        
        output_path, _ = QFileDialog.getSaveFileName(
            self, '导出图片', default_name, ext_filter
        )
        
        if not output_path:
            return
        
        # Determine format from extension
        ext = os.path.splitext(output_path)[1].lower()
        fmt = 'JPEG' if ext in ('.jpg', '.jpeg') else 'PNG'
        
        # Get target resolution
        target_long_edge = self.controls.get_export_resolution()
        
        try:
            # Render at full resolution
            self.status_bar.showMessage('正在渲染...')
            QApplication.processEvents()
            
            # If Original resolution, use the source image's long edge
            if target_long_edge <= 0:
                from PIL import Image as PILImage
                try:
                    with PILImage.open(self._current_filepath) as src_img:
                        target_long_edge = max(src_img.width, src_img.height)
                except Exception:
                    target_long_edge = 4096
            
            params = self._build_render_params()
            result = process_image(
                self._current_filepath,
                template_key=self.controls.get_template_key(),
                ratio_key=self.controls.get_ratio_key(),
                target_long_edge=target_long_edge,
                render_params=params,
                exif_data=self._get_exif(self._current_filepath),
            )
            
            if result is None:
                QMessageBox.critical(self, '错误', '渲染失败')
                return
            
            rendered_img, merged, exif_src = result
            
            # Export
            success = export_image(
                rendered_img,
                output_path,
                format=fmt,
                quality=95,
                target_long_edge=0,  # Already sized during render
            )
            
            if success:
                self.status_bar.showMessage(f'已导出: {os.path.basename(output_path)}')
                QMessageBox.information(
                    self, '导出成功',
                    f'图片已保存到:\n{output_path}\n\n'
                    f'尺寸: {rendered_img.size[0]}x{rendered_img.size[1]}'
                )
            else:
                QMessageBox.critical(self, '错误', f'导出失败，请检查路径是否可写:\n{output_path}')
        
        except Exception as e:
            logger.error(f'Export error: {e}')
            QMessageBox.critical(self, '导出错误', str(e))
    
    def _apply_style(self):
        """Apply application-wide stylesheet."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #000000;
            }
            QWidget {
                background-color: #000000;
                color: #F2F2F7;
                font-family: "Segoe UI";
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #2C2C2E;
                border-radius: 14px;
                margin-top: 12px;
                padding: 16px 12px 12px 12px;
                background: #1C1C1E;
                color: #F2F2F7;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 8px;
                color: #F2F2F7;
                background: #000000;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QLabel {
                color: #F2F2F7;
                background: transparent;
            }
            QLineEdit, QComboBox, QListWidget {
                background-color: #2C2C2E;
                color: #F2F2F7;
                border: 1px solid #3A3A3C;
                border-radius: 10px;
                padding: 7px 10px;
                selection-background-color: #0A84FF;
                selection-color: #FFFFFF;
            }
            QLineEdit:focus, QComboBox:focus, QListWidget:focus {
                border: 1px solid #0A84FF;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                background-color: #2C2C2E;
                color: #F2F2F7;
                border: 1px solid #3A3A3C;
                selection-background-color: #0A84FF;
            }
            QListWidget {
                padding: 4px;
            }
            QListWidget::item {
                border-radius: 8px;
                padding: 7px 8px;
            }
            QListWidget::item:selected {
                background-color: #0A84FF;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #2C2C2E;
                color: #F2F2F7;
                border: 1px solid #3A3A3C;
                border-radius: 12px;
                padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #3A3A3C;
            }
            QPushButton:pressed {
                background-color: #48484A;
            }
            QPushButton#primaryButton {
                background-color: #0A84FF;
                border: 1px solid #0A84FF;
                color: #FFFFFF;
            }
            QCheckBox {
                color: #F2F2F7;
                spacing: 8px;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 1px solid #636366;
                background-color: #2C2C2E;
            }
            QCheckBox::indicator:checked {
                background-color: #0A84FF;
                border: 1px solid #0A84FF;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #3A3A3C;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #0A84FF;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                width: 18px;
                height: 18px;
                background: #F2F2F7;
                border: 1px solid #C7C7CC;
                border-radius: 9px;
                margin: -7px 0;
            }
            QSplitter::handle {
                background: #1C1C1E;
                width: 1px;
            }
            QStatusBar {
                background: #1C1C1E;
                color: #C7C7CC;
                border-top: 1px solid #2C2C2E;
            }
        """)
    
    def dragEnterEvent(self, event):
        """Accept drag events at window level."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handle drops anywhere in the main window."""
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            ext = os.path.splitext(path)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                files.append(path)
        if files:
            self.image_list.add_files(files)
            event.acceptProposedAction()
