"""Main window for the EXIF frame app."""

import os
import logging
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter,
    QMessageBox, QFileDialog, QStatusBar,
)
from PySide6.QtCore import Qt, QTimer, QObject, QRunnable, QThreadPool, Signal, Slot

from src.ui.image_list import ImageListPanel, SUPPORTED_EXTENSIONS
from src.ui.preview import PreviewPanel
from src.ui.controls import ControlsPanel
from src.core.image_processor import process_image, process_preview
from src.core.exporter import export_image, generate_output_filename
from src.core.local_cache import get_cached_exif, set_cached_exif
from src.templates.base import RenderParams

logger = logging.getLogger(__name__)


class PreviewWorkerSignals(QObject):
    finished = Signal(int, str, tuple, object)
    failed = Signal(int, str, str)


class PreviewWorker(QRunnable):
    """Render a preview off the UI thread."""

    def __init__(
        self,
        request_id: int,
        filepath: str,
        cache_key: tuple,
        template_key: str,
        ratio_key: str,
        params: RenderParams,
        preview_long_edge: int,
        exif_data: dict,
    ):
        super().__init__()
        self.request_id = request_id
        self.filepath = filepath
        self.cache_key = cache_key
        self.template_key = template_key
        self.ratio_key = ratio_key
        self.params = params
        self.preview_long_edge = preview_long_edge
        self.exif_data = dict(exif_data)
        self.signals = PreviewWorkerSignals()

    @Slot()
    def run(self):
        try:
            preview_img = process_preview(
                self.filepath,
                template_key=self.template_key,
                ratio_key=self.ratio_key,
                render_params=self.params,
                preview_long_edge=self.preview_long_edge,
                exif_data=self.exif_data,
            )
            self.signals.finished.emit(
                self.request_id, self.filepath, self.cache_key, preview_img
            )
        except Exception as e:
            self.signals.failed.emit(self.request_id, self.filepath, str(e))


class ExportWorkerSignals(QObject):
    finished = Signal(int, str, int, int)
    failed = Signal(int, str)


class ExportWorker(QRunnable):
    """Render and export without blocking the UI."""

    def __init__(
        self,
        request_id: int,
        filepath: str,
        output_path: str,
        fmt: str,
        template_key: str,
        ratio_key: str,
        params: RenderParams,
        target_long_edge: int,
        exif_data: dict,
    ):
        super().__init__()
        self.request_id = request_id
        self.filepath = filepath
        self.output_path = output_path
        self.fmt = fmt
        self.template_key = template_key
        self.ratio_key = ratio_key
        self.params = params
        self.target_long_edge = target_long_edge
        self.exif_data = dict(exif_data)
        self.signals = ExportWorkerSignals()

    @Slot()
    def run(self):
        try:
            target_long_edge = self.target_long_edge
            if target_long_edge <= 0:
                from PIL import Image as PILImage
                try:
                    with PILImage.open(self.filepath) as src_img:
                        target_long_edge = max(src_img.width, src_img.height)
                except Exception:
                    target_long_edge = 4096

            result = process_image(
                self.filepath,
                template_key=self.template_key,
                ratio_key=self.ratio_key,
                target_long_edge=target_long_edge,
                render_params=self.params,
                exif_data=self.exif_data,
            )
            if result is None:
                self.signals.failed.emit(self.request_id, 'The image could not be rendered.')
                return

            rendered_img, _merged, _exif_src = result
            success = export_image(
                rendered_img, self.output_path,
                format=self.fmt, quality=95, target_long_edge=0
            )
            if not success:
                self.signals.failed.emit(
                    self.request_id, 'Check whether the destination is writable.'
                )
                return
            self.signals.finished.emit(
                self.request_id, self.output_path,
                rendered_img.size[0], rendered_img.size[1],
            )
        except Exception as e:
            self.signals.failed.emit(self.request_id, str(e))


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('EXIF Frame Card')
        self.setMinimumSize(1200, 750)
        self.resize(1450, 860)
        self.setAcceptDrops(True)

        self._current_filepath: Optional[str] = None
        self._exif_cache: dict[str, dict] = {}
        self._preview_cache: dict[tuple, object] = {}
        self._pending_filepath: Optional[str] = None
        self._render_state_by_file: dict[str, dict] = {}
        self._metadata_state_by_file: dict[str, dict] = {}
        self._default_render_state: dict = {}
        self._batch_render_state: dict = {}
        self._loading_controls = False
        self._preview_request_id = 0
        self._preview_busy = False
        self._preview_queued = False
        self._export_request_id = 0
        self._thread_pool = QThreadPool.globalInstance()
        self._thread_pool.setMaxThreadCount(1)

        self._selection_timer = QTimer(singleShot=True, interval=20, timeout=self._apply_pending_selection)
        self._update_timer = QTimer(singleShot=True, interval=90, timeout=self._update_preview)

        self._setup_ui()
        self._default_render_state = self.controls.get_render_state()
        self._batch_render_state = dict(self._default_render_state)
        self._connect_signals()
        self._apply_style()

    def _setup_ui(self):
        central = QWidget()
        central.setObjectName('AppRoot')
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName('MainSplitter')
        splitter.setHandleWidth(1)

        self.image_list = ImageListPanel()
        self.preview = PreviewPanel()
        self.controls = ControlsPanel()

        splitter.addWidget(self.image_list)
        splitter.addWidget(self.preview)
        splitter.addWidget(self.controls)
        splitter.setSizes([292, 830, 328])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)

        main_layout.addWidget(splitter)

        self.status_bar = QStatusBar()
        self.status_bar.setObjectName('AppStatusBar')
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('Ready. Import photos or drop them into the window.')

    def _connect_signals(self):
        self.image_list.image_selected.connect(self._on_image_selected)
        self.controls.params_changed.connect(self._on_controls_changed)
        self.preview.export_requested.connect(self._on_export)

    def _on_image_selected(self, filepath: str):
        self._pending_filepath = filepath
        self._selection_timer.start()

    def _apply_pending_selection(self):
        filepath = self._pending_filepath
        if not filepath or filepath == self._current_filepath:
            return

        self._save_current_control_state()
        self._current_filepath = filepath
        self.status_bar.showMessage(f'Selected: {os.path.basename(filepath)}')
        self.preview.set_quick_preview(filepath)
        exif_data = self._get_exif(filepath)
        self._load_control_state(filepath, exif_data)
        self._schedule_preview_update(0)

    def _metadata_from_exif(self, exif_data: dict) -> dict:
        state = {key: '' for key in [
            'title', 'location', 'camera', 'lens', 'focal_length',
            'aperture', 'shutter_speed', 'iso', 'date',
            'postcard_header',
        ]}
        state['postcard_header'] = 'CARTE POSTALE'
        for key in ['camera', 'lens', 'focal_length', 'aperture',
                    'shutter_speed', 'iso', 'date', 'location']:
            state[key] = exif_data.get(key, '')
        return state

    def _load_control_state(self, filepath: str, exif_data: dict):
        self._loading_controls = True
        try:
            if self.controls.get_batch_mode():
                render_state = self._batch_render_state
            else:
                render_state = self._render_state_by_file.setdefault(
                    filepath, dict(self._default_render_state)
                )
            metadata_state = self._metadata_state_by_file.setdefault(
                filepath, self._metadata_from_exif(exif_data)
            )
            self.controls.set_render_state(render_state)
            self.controls.set_metadata_state(metadata_state)
        finally:
            self._loading_controls = False

    def _save_current_control_state(self):
        if not self._current_filepath or self._loading_controls:
            return
        self._metadata_state_by_file[self._current_filepath] = self.controls.get_metadata_state()
        render_state = self.controls.get_render_state()
        if self.controls.get_batch_mode():
            self._batch_render_state = dict(render_state)
            for filepath in self.image_list.get_all_filepaths():
                self._render_state_by_file[filepath] = dict(render_state)
        else:
            self._render_state_by_file[self._current_filepath] = dict(render_state)

    def _on_controls_changed(self):
        if self._loading_controls:
            return
        self._save_current_control_state()
        self._schedule_preview_update()

    def _get_exif(self, filepath: str) -> dict:
        if filepath not in self._exif_cache:
            from src.core.exif_reader import read_exif
            cached = get_cached_exif(filepath)
            if cached is None:
                cached = read_exif(filepath)
                set_cached_exif(filepath, cached)
            self._exif_cache[filepath] = cached
        return self._exif_cache[filepath]

    def _preview_cache_key(self, filepath: str, params: RenderParams) -> tuple:
        return (
            filepath,
            self.controls.get_template_key(),
            self.controls.get_ratio_key(),
            self.controls.get_preview_long_edge(),
            params.ratio,
            params.bg_color,
            params.margin_top, params.margin_side, params.margin_bottom,
            params.image_corner_radius, params.image_shadow,
            params.image_zoom, params.image_offset_x, params.image_offset_y,
            params.font_size, params.font_color, params.font_bold,
            params.text_align,
            params.postcard_header_size,
            params.postcard_header_color,
            params.postcard_header_bold,
            params.logo_enabled, params.logo_size, params.logo_position,
            params.qr_enabled, params.qr_size, params.qr_position,
            params.map_provider,
            params.title, params.location, params.camera, params.lens,
            params.focal_length, params.aperture, params.shutter_speed,
            params.iso, params.date, params.postcard_header,
        )

    def _remember_preview(self, key: tuple, preview_img):
        self._preview_cache[key] = preview_img
        if len(self._preview_cache) > 3:
            self._preview_cache.pop(next(iter(self._preview_cache)), None)

    def _schedule_preview_update(self, delay_ms: int = 90):
        self._update_timer.setInterval(delay_ms)
        self._update_timer.start()

    def _update_preview(self):
        if not self._current_filepath:
            return
        if self._preview_busy:
            self._preview_queued = True
            return

        try:
            params = self._build_render_params()
            cache_key = self._preview_cache_key(self._current_filepath, params)
            cached = self._preview_cache.get(cache_key)
            if cached is not None:
                self.preview.set_preview(cached)
                self.status_bar.showMessage(f'Preview updated: {os.path.basename(self._current_filepath)}')
                return

            self._preview_request_id += 1
            request_id = self._preview_request_id
            filepath = self._current_filepath
            self._preview_busy = True
            self.status_bar.showMessage(f'Rendering preview: {os.path.basename(filepath)}')

            worker = PreviewWorker(
                request_id,
                filepath,
                cache_key,
                self.controls.get_template_key(),
                self.controls.get_ratio_key(),
                params,
                self.controls.get_preview_long_edge(),
                self._get_exif(filepath),
            )
            worker.signals.finished.connect(self._on_preview_ready)
            worker.signals.failed.connect(self._on_preview_failed)
            self._thread_pool.start(worker)
        except Exception as e:
            self._preview_busy = False
            logger.error(f'Preview dispatch error: {e}')
            self.status_bar.showMessage(f'Preview error: {e}')

    def _on_preview_ready(self, request_id: int, filepath: str, cache_key: tuple, preview_img):
        self._preview_busy = False
        if request_id != self._preview_request_id or filepath != self._current_filepath:
            self._run_queued_preview_if_needed()
            return
        if preview_img is None:
            self.status_bar.showMessage(f'Preview unavailable: {os.path.basename(filepath)}')
            self._run_queued_preview_if_needed()
            return
        self._remember_preview(cache_key, preview_img)
        self.preview.set_preview(preview_img)
        self.status_bar.showMessage(f'Preview updated: {os.path.basename(filepath)}')
        self._run_queued_preview_if_needed()

    def _on_preview_failed(self, request_id: int, filepath: str, message: str):
        self._preview_busy = False
        if request_id != self._preview_request_id or filepath != self._current_filepath:
            self._run_queued_preview_if_needed()
            return
        logger.error(f'Preview error: {message}')
        self.status_bar.showMessage(f'Preview error: {message}')
        self._run_queued_preview_if_needed()

    def _run_queued_preview_if_needed(self):
        if self._preview_queued:
            self._preview_queued = False
            self._schedule_preview_update(0)

    def _build_render_params(self) -> RenderParams:
        ratio_key = self.controls.get_ratio_key()
        ratio_map = {
            'Original': None,
            '1:1': (1, 1), '4:5': (4, 5), '3:4': (3, 4),
            '16:9': (16, 9), '9:16': (9, 16),
            'A4 Portrait': (210, 297), 'A4 Landscape': (297, 210),
        }
        ratio = ratio_map.get(ratio_key, (4, 5))
        if ratio is None and self._current_filepath:
            from PIL import Image
            from math import gcd
            try:
                img = Image.open(self._current_filepath)
                g = gcd(img.width, img.height)
                ratio = (img.width // g, img.height // g)
            except Exception:
                ratio = (3, 2)

        return RenderParams(
            ratio=ratio or (3, 2),
            bg_color=self.controls.get_bg_color(),
            margin_top=self.controls.get_margin('margin_top'),
            margin_side=self.controls.get_margin('margin_side'),
            margin_bottom=self.controls.get_margin('margin_bottom'),
            image_corner_radius=self.controls.get_margin('image_corner_radius'),
            image_shadow=self.controls.get_shadow(),
            image_zoom=self.controls.get_margin('image_zoom'),
            image_offset_x=self.controls.get_margin('image_offset_x'),
            image_offset_y=self.controls.get_margin('image_offset_y'),
            font_size=self.controls.get_font_size(),
            font_color=self.controls.get_font_color(),
            font_bold=self.controls.get_font_bold(),
            text_align=self.controls.get_text_align(),
            postcard_header_size=self.controls.get_postcard_header_size(),
            postcard_header_color=self.controls.get_postcard_header_color(),
            postcard_header_bold=self.controls.get_postcard_header_bold(),
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
            note='',
            postcard_header=self.controls.get_exif_field('postcard_header') or 'CARTE POSTALE',
        )

    def _on_export(self):
        if not self._current_filepath:
            QMessageBox.warning(self, 'No Photo Selected', 'Import a photo before exporting.')
            return

        export_format = self.controls.get_export_format()
        ext_filter = 'JPEG (*.jpg);;PNG (*.png)' if export_format == 'JPEG' else 'PNG (*.png);;JPEG (*.jpg)'
        default_name = generate_output_filename(
            self._current_filepath, '_framed',
            '.jpg' if export_format == 'JPEG' else '.png'
        )
        output_path, _ = QFileDialog.getSaveFileName(self, 'Export Image', default_name, ext_filter)
        if not output_path:
            return

        ext = os.path.splitext(output_path)[1].lower()
        fmt = 'JPEG' if ext in ('.jpg', '.jpeg') else 'PNG'
        target_long_edge = self.controls.get_export_resolution()

        try:
            self._export_request_id += 1
            request_id = self._export_request_id
            params = self._build_render_params()
            worker = ExportWorker(
                request_id,
                self._current_filepath,
                output_path,
                fmt,
                self.controls.get_template_key(),
                self.controls.get_ratio_key(),
                params,
                target_long_edge,
                self._get_exif(self._current_filepath),
            )
            worker.signals.finished.connect(self._on_export_ready)
            worker.signals.failed.connect(self._on_export_failed)
            self.preview.set_exporting(True, 'Exporting...')
            self.status_bar.showMessage(f'Exporting: {os.path.basename(output_path)}')
            self._thread_pool.start(worker)
        except Exception as e:
            logger.error(f'Export error: {e}')
            self.preview.set_exporting(False, '')
            QMessageBox.critical(self, 'Export Error', str(e))

    def _on_export_ready(self, request_id: int, output_path: str, width: int, height: int):
        if request_id != self._export_request_id:
            return
        filename = os.path.basename(output_path)
        self.preview.show_export_done('Exported')
        self.status_bar.showMessage(f'Exported: {filename} ({width}x{height})')

    def _on_export_failed(self, request_id: int, message: str):
        if request_id != self._export_request_id:
            return
        self.preview.set_exporting(False, '')
        logger.error(f'Export error: {message}')
        self.status_bar.showMessage(f'Export failed: {message}')
        QMessageBox.critical(self, 'Export Failed', message)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            ext = os.path.splitext(path)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                paths.append(path)
        if paths:
            self.image_list.add_files(paths)
            self.image_list.select_last()
            event.acceptProposedAction()

    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow, QWidget#AppRoot {
                background: #FFFFFF;
                color: #242426;
                font-family: "Segoe UI", "SF Pro Text", Arial, sans-serif;
                font-size: 13px;
            }
            QWidget#ImageListPanel {
                background: #F4F4F5;
                border-right: 1px solid #E4E4E7;
            }
            QWidget#ControlsPanel {
                background: #FFFFFF;
                border-left: 1px solid #E4E4E7;
            }
            QWidget#PreviewPanel {
                background: #FFFFFF;
            }
            QScrollArea#ControlsScroll {
                border: none;
                background: #FFFFFF;
            }
            QWidget#ControlsContent {
                background: #FFFFFF;
            }
            QLabel {
                color: #242426;
                background: transparent;
            }
            QLabel#SidebarTitle, QLabel#PreviewTitle {
                color: #18181B;
                font-size: 15px;
                font-weight: 650;
            }
            QLabel#ExportStatus {
                color: #71717A;
                font-size: 12px;
                font-weight: 500;
            }
            QProgressBar#ExportProgress {
                background: #E4E4E7;
                border: none;
                border-radius: 3px;
            }
            QProgressBar#ExportProgress::chunk {
                background: #18181B;
                border-radius: 3px;
            }
            QLabel#SectionTitle {
                color: #71717A;
                font-size: 11px;
                font-weight: 650;
                padding-left: 3px;
                text-transform: uppercase;
            }
            QLabel#FieldLabel {
                color: #71717A;
                font-size: 11px;
                font-weight: 500;
            }
            QLabel#ValueLabel {
                color: #71717A;
                font-size: 11px;
                min-width: 34px;
            }
            QFrame#ControlCard {
                background: #FAFAFA;
                border: 1px solid #E4E4E7;
                border-radius: 12px;
            }
            QLineEdit, QComboBox {
                background: #FFFFFF;
                color: #242426;
                border: 1px solid #D4D4D8;
                border-radius: 9px;
                min-height: 24px;
                padding: 3px 8px;
                selection-background-color: #D9ECFF;
                selection-color: #18181B;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #9CA3AF;
                background: #FFFFFF;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                background: #FFFFFF;
                color: #242426;
                border: 1px solid #D4D4D8;
                border-radius: 8px;
                selection-background-color: #F4F4F5;
            }
            QPushButton {
                background: #FFFFFF;
                color: #3F3F46;
                border: 1px solid #D4D4D8;
                border-radius: 9px;
                min-height: 24px;
                padding: 3px 10px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #F4F4F5;
            }
            QPushButton:pressed {
                background: #E4E4E7;
            }
            QPushButton#primaryButton {
                background: #18181B;
                border-color: #18181B;
                color: #FFFFFF;
            }
            QPushButton#primaryButton:hover {
                background: #27272A;
            }
            QPushButton#ColorSwatch {
                border: 1px solid #D4D4D8;
                border-radius: 8px;
                padding: 0;
                min-height: 0;
            }
            QCheckBox {
                color: #3F3F46;
                spacing: 8px;
                background: transparent;
                min-height: 20px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid #A1A1AA;
                background: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                background: #18181B;
                border-color: #18181B;
            }
            QSlider {
                min-height: 24px;
                background: transparent;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #E4E4E7;
                border-radius: 3px;
                margin: 9px 0;
            }
            QSlider::sub-page:horizontal {
                background: #18181B;
                border-radius: 3px;
                margin: 9px 0;
            }
            QSlider::add-page:horizontal {
                background: #E4E4E7;
                border-radius: 3px;
                margin: 9px 0;
            }
            QSlider::handle:horizontal {
                width: 22px;
                height: 22px;
                background: #FFFFFF;
                border: 1px solid #C7C7CC;
                border-radius: 11px;
                margin: -8px 0;
            }
            QSlider::handle:horizontal:hover {
                border: 1px solid #A1A1AA;
                background: #FFFFFF;
            }
            QSlider::handle:horizontal:pressed {
                border: 1px solid #71717A;
                background: #F4F4F5;
            }
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
                padding: 2px;
            }
            QListWidget::item {
                color: #3F3F46;
                border: none;
                border-radius: 10px;
                min-height: 64px;
                padding: 0;
            }
            QListWidget::item:hover {
                background: #EDEDEF;
            }
            QListWidget::item:selected {
                background: #E9E9EB;
                color: #18181B;
            }
            QWidget#PhotoListRow {
                background: transparent;
            }
            QLabel#PhotoName {
                color: #27272A;
                font-size: 12px;
                background: transparent;
            }
            QLabel#PhotoThumb {
                background: transparent;
                border: none;
            }
            QSplitter::handle {
                background: #E4E4E7;
            }
            QStatusBar#AppStatusBar {
                background: #FFFFFF;
                color: #71717A;
                border-top: 1px solid #E4E4E7;
            }
        """)
