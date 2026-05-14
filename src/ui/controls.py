"""Right Panel — Liquid Glass minimal controls."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QSlider,
    QPushButton, QGroupBox, QScrollArea, QHBoxLayout, QCheckBox,
    QColorDialog,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor


class ControlsPanel(QWidget):
    params_changed = Signal()
    export_format_changed = Signal(str)
    export_resolution_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(270)
        self.setMaximumWidth(370)
        self._bg_color = (250, 249, 245)
        self._font_color = (80, 80, 80)
        self._setup_ui()

    # ── UI layout ─────────────────────────────────────────────────────
    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')

        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(14, 16, 14, 16)
        layout.setSpacing(14)

        # Template
        layout.addWidget(self._section('模板', [
            self._combo('template', [
                ('museum_white', 'Museum White'),
                ('gallery_black', 'Gallery Black'),
                ('offwhite_archive', 'Off-white Archive'),
                ('minimal_border', 'Minimal Border'),
                ('contact_sheet', 'Vintage Postcard'),
            ]),
        ]))
        # Ratio
        layout.addWidget(self._section('画布比例', [
            self._combo('ratio', [
                ('Original', 'Original'), ('1:1', '1:1'), ('4:5', '4:5'),
                ('3:4', '3:4'), ('16:9', '16:9'), ('9:16', '9:16'),
                ('A4 Portrait', 'A4 Portrait'), ('A4 Landscape', 'A4 Landscape'),
            ]),
        ]))

        # ══ EXIF fields ══
        exif_group = QGroupBox('EXIF 信息')
        exif_layout = QVBoxLayout(exif_group)
        exif_layout.setSpacing(6)

        self.exif_fields = {}
        for key, label in [
            ('title', '标题'), ('location', '地点'), ('camera', '相机'),
            ('lens', '镜头'), ('focal_length', '焦距'), ('aperture', '光圈'),
            ('shutter_speed', '快门'), ('iso', 'ISO'), ('date', '日期'), ('note', '备注'),
        ]:
            row = QHBoxLayout()
            row.setSpacing(8)
            lbl = QLabel(label)
            lbl.setFixedWidth(36)
            lbl.setStyleSheet('font-size:11px; color:#AEAEB2;')
            edit = QLineEdit()
            edit.setPlaceholderText('—')
            edit.textChanged.connect(lambda _v: self.params_changed.emit())
            row.addWidget(lbl)
            row.addWidget(edit, 1)
            exif_layout.addLayout(row)
            self.exif_fields[key] = edit

        layout.addWidget(exif_group)

        # ══ Border ══
        border_group = QGroupBox('边框')
        border_layout = QVBoxLayout(border_group)
        border_layout.setSpacing(8)

        # bg color
        bg_row = QHBoxLayout()
        bg_row.addWidget(QLabel('背景色'))
        bg_row.setSpacing(8)
        self.bg_swatch = QPushButton()
        self.bg_swatch.setObjectName('colorSwatch')
        self.bg_swatch.setStyleSheet(
            f'QPushButton#colorSwatch {{ background-color:rgb{self._bg_color}; }}')
        self.bg_swatch.clicked.connect(self._pick_bg)
        bg_row.addWidget(self.bg_swatch)
        bg_row.addStretch()
        border_layout.addLayout(bg_row)

        for key, label, mn, mx, dv in [
            ('margin_top', '上留白', 0, 300, 60),
            ('margin_side', '左右留白', 0, 300, 80),
            ('margin_bottom', '下留白', 0, 400, 120),
            ('image_corner_radius', '圆角', 0, 100, 0),
        ]:
            border_layout.addWidget(self._slider(key, label, mn, mx, dv))

        self.shadow_check = QCheckBox('投影')
        self.shadow_check.stateChanged.connect(lambda _v: self.params_changed.emit())
        border_layout.addWidget(self.shadow_check)

        sep = QLabel('字体')
        sep.setStyleSheet('font-weight:600; color:#6E6E73; margin-top:4px;')
        border_layout.addWidget(sep)

        border_layout.addWidget(self._slider('font_size', '大小', 8, 48, 18))

        fc_row = QHBoxLayout()
        fc_row.addWidget(QLabel('颜色'))
        fc_row.setSpacing(8)
        self.fc_swatch = QPushButton()
        self.fc_swatch.setObjectName('colorSwatch')
        self.fc_swatch.setStyleSheet(
            f'QPushButton#colorSwatch {{ background-color:rgb{self._font_color}; }}')
        self.fc_swatch.clicked.connect(self._pick_font_color)
        fc_row.addWidget(self.fc_swatch)
        fc_row.addStretch()
        border_layout.addLayout(fc_row)

        self.bold_check = QCheckBox('粗体')
        self.bold_check.stateChanged.connect(lambda _v: self.params_changed.emit())
        border_layout.addWidget(self.bold_check)

        border_layout.addWidget(self._combo('text_align', [
            ('left', '左对齐'), ('center', '居中'), ('right', '右对齐'),
        ], label='文字对齐'))

        layout.addWidget(border_group)

        # ══ Logo & QR ══
        extras_group = QGroupBox('Logo & QR')
        extras_layout = QVBoxLayout(extras_group)
        extras_layout.setSpacing(8)

        self.logo_check = QCheckBox('相机品牌 Logo')
        self.logo_check.setChecked(True)
        self.logo_check.stateChanged.connect(lambda _v: self.params_changed.emit())
        extras_layout.addWidget(self.logo_check)

        extras_layout.addWidget(self._slider('logo_size', 'Logo 大小', 40, 180, 90))
        extras_layout.addWidget(self._combo('logo_position', [
            ('bottom_right', '右下'), ('bottom_left', '左下'),
            ('top_right', '右上'), ('top_left', '左上'),
        ], label='Logo 位置'))

        self.qr_check = QCheckBox('GPS 地图二维码')
        self.qr_check.setChecked(True)
        self.qr_check.stateChanged.connect(lambda _v: self.params_changed.emit())
        extras_layout.addWidget(self.qr_check)

        extras_layout.addWidget(self._slider('qr_size', '码大小', 40, 180, 86))
        extras_layout.addWidget(self._combo('qr_position', [
            ('bottom_left', '左下'), ('bottom_right', '右下'),
            ('top_left', '左上'), ('top_right', '右上'),
        ], label='码位置'))
        extras_layout.addWidget(self._combo('map_provider', [
            ('apple', 'Apple Maps'), ('google', 'Google Maps'), ('geo', '通用 geo'),
        ], label='地图服务'))

        layout.addWidget(extras_group)

        # ══ Export ══
        export_group = QGroupBox('导出')
        export_layout = QVBoxLayout(export_group)
        export_layout.setSpacing(8)

        export_layout.addWidget(self._combo('export_format', [
            ('JPEG', 'JPG'), ('PNG', 'PNG'),
        ], label='格式'))

        export_layout.addWidget(self._combo('export_resolution', [
            ('1080', '1080px 长边'), ('2048', '2048px 长边'),
            ('3000', '3000px 长边'), ('0', '原始高清'),
        ], label='分辨率'))

        layout.addWidget(export_group)
        layout.addStretch()

        scroll.setWidget(w)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # Wire combo changes → params_changed (only once)
        for name in ['template', 'ratio', 'text_align', 'logo_position',
                     'qr_position', 'map_provider']:
            getattr(self, f'_combo_{name}').currentTextChanged.connect(
                lambda _v: self.params_changed.emit())

        self._combo_export_format.currentIndexChanged.connect(
            lambda _idx: self.export_format_changed.emit(self._combo_val('export_format')))
        self._combo_export_resolution.currentIndexChanged.connect(
            lambda _idx: self._on_resolution())

        # Set default selections
        self._combo_ratio.setCurrentIndex(2)       # 4:5
        self._combo_export_resolution.setCurrentIndex(1)  # 2048px

    # ── Widget helpers ───────────────────────────────────────────────
    def _section(self, title: str, widgets: list) -> QGroupBox:
        g = QGroupBox(title)
        gl = QVBoxLayout(g)
        gl.setSpacing(8)
        for w in widgets:
            gl.addWidget(w)
        return g

    def _combo(self, name: str, items: list, label: str = '') -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        if label:
            lbl = QLabel(label)
            lbl.setFixedWidth(55)
            lbl.setStyleSheet('font-size:11px; color:#AEAEB2;')
            lay.addWidget(lbl)
        cb = QComboBox()
        for val, disp in items:
            cb.addItem(disp, val)
        lay.addWidget(cb, 1)
        setattr(self, f'_combo_{name}', cb)
        return w

    def _slider(self, name: str, label: str, mn: int, mx: int, dv: int) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        lbl = QLabel(label)
        lbl.setFixedWidth(55)
        lbl.setStyleSheet('font-size:11px; color:#AEAEB2;')

        slider = QSlider(Qt.Horizontal)
        slider.setRange(mn, mx)
        slider.setValue(dv)
        slider.valueChanged.connect(lambda _v: self.params_changed.emit())

        val = QLabel(str(dv))
        val.setFixedWidth(30)
        val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        val.setStyleSheet('font-size:11px; color:#6E6E73;')
        slider.valueChanged.connect(lambda v: val.setText(str(v)))

        lay.addWidget(lbl)
        lay.addWidget(slider, 1)
        lay.addWidget(val)

        if not hasattr(self, '_sliders'):
            self._sliders = {}
        self._sliders[name] = slider
        return w

    # ── Color pickers ────────────────────────────────────────────────
    def _pick_bg(self):
        c = QColorDialog.getColor(QColor(*self._bg_color), self, '背景色')
        if c.isValid():
            self._bg_color = (c.red(), c.green(), c.blue())
            self.bg_swatch.setStyleSheet(
                f'QPushButton#colorSwatch {{ background-color:rgb{self._bg_color}; }}')
            self.params_changed.emit()

    def _pick_font_color(self):
        c = QColorDialog.getColor(QColor(*self._font_color), self, '字体色')
        if c.isValid():
            self._font_color = (c.red(), c.green(), c.blue())
            self.fc_swatch.setStyleSheet(
                f'QPushButton#colorSwatch {{ background-color:rgb{self._font_color}; }}')
            self.params_changed.emit()

    def _on_resolution(self):
        self.export_resolution_changed.emit(int(self._combo_val('export_resolution') or 2048))

    # ── Getters ──────────────────────────────────────────────────────
    def _combo_val(self, name: str) -> str:
        cb = getattr(self, f'_combo_{name}', None)
        return cb.currentData() if cb else ''

    def _slider_val(self, name: str, default: int = 0) -> int:
        if not hasattr(self, '_sliders'):
            return default
        s = self._sliders.get(name)
        return s.value() if s else default

    def get_template_key(self) -> str:
        return self._combo_val('template') or 'museum_white'

    def get_ratio_key(self) -> str:
        return self._combo_val('ratio') or '4:5'

    def get_bg_color(self) -> tuple:
        return self._bg_color

    def get_font_color(self) -> tuple:
        return self._font_color

    def get_margin(self, key: str) -> int:
        return self._slider_val(key, 0)

    def get_shadow(self) -> bool:
        return self.shadow_check.isChecked() if hasattr(self, 'shadow_check') else False

    def get_font_size(self) -> int:
        return self._slider_val('font_size', 18)

    def get_font_bold(self) -> bool:
        return self.bold_check.isChecked() if hasattr(self, 'bold_check') else False

    def get_text_align(self) -> str:
        return self._combo_val('text_align') or 'left'

    def get_logo_enabled(self) -> bool:
        return self.logo_check.isChecked() if hasattr(self, 'logo_check') else True

    def get_logo_size(self) -> int:
        return self._slider_val('logo_size', 90)

    def get_logo_position(self) -> str:
        return self._combo_val('logo_position') or 'bottom_right'

    def get_qr_enabled(self) -> bool:
        return self.qr_check.isChecked() if hasattr(self, 'qr_check') else True

    def get_qr_size(self) -> int:
        return self._slider_val('qr_size', 86)

    def get_qr_position(self) -> str:
        return self._combo_val('qr_position') or 'bottom_left'

    def get_map_provider(self) -> str:
        return self._combo_val('map_provider') or 'apple'

    def get_exif_field(self, key: str) -> str:
        e = self.exif_fields.get(key)
        return e.text() if e else ''

    def set_exif_field(self, key: str, value: str, overwrite: bool = False):
        e = self.exif_fields.get(key)
        if e and (overwrite or not e.text()):
            e.blockSignals(True)
            e.setText(value or '')
            e.blockSignals(False)

    def set_all_exif_fields(self, exif_data: dict, overwrite: bool = False):
        for key in ['camera', 'lens', 'focal_length', 'aperture',
                     'shutter_speed', 'iso', 'date', 'location']:
            self.set_exif_field(key, exif_data.get(key, ''), overwrite=overwrite)

    def get_export_format(self) -> str:
        return self._combo_val('export_format') or 'JPEG'

    def get_export_resolution(self) -> int:
        return int(self._combo_val('export_resolution') or 2048)
