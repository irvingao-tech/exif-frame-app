"""
Right Panel: Controls
Template selection, ratio, EXIF editing, border params, export settings.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QSlider,
    QPushButton, QGroupBox, QScrollArea, QHBoxLayout, QCheckBox,
    QSpinBox, QColorDialog,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor


class ControlsPanel(QWidget):
    """Right panel: all editing controls."""
    
    # Signals when any parameter changes
    params_changed = Signal()
    export_format_changed = Signal(str)  # 'JPEG' or 'PNG'
    export_resolution_changed = Signal(int)  # target long edge
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(280)
        self.setMaximumWidth(380)
        self._bg_color = (250, 249, 245)
        self._font_color = (80, 80, 80)
        self._setup_ui()
    
    def _setup_ui(self):
        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        
        # --- Template Selection ---
        layout.addWidget(self._make_group('模板风格', [
            self._make_combo('template', '模板', [
                'museum_white', 'gallery_black', 'offwhite_archive',
                'minimal_border', 'contact_sheet',
            ], [
                'Museum White 美术馆白',
                'Gallery Black 画廊黑',
                'Off-white Archive 档案卡',
                'Minimal Border 极简边框',
                'Vintage Postcard 复古明信片',
            ]),
        ]))
        
        # --- Ratio ---
        layout.addWidget(self._make_group('画布比例', [
            self._make_combo('ratio', '比例', [
                'Original', '1:1', '4:5', '3:4', '16:9', '9:16',
                'A4 Portrait', 'A4 Landscape',
            ]),
        ]))
        
        # --- EXIF Info Editing ---
        exif_group = QGroupBox('EXIF 信息编辑')
        exif_group.setFont(QFont('Segoe UI', 10, QFont.Bold))
        exif_layout = QVBoxLayout(exif_group)
        exif_layout.setSpacing(4)
        
        self.exif_fields = {}
        field_labels = [
            ('title', '标题 Title'),
            ('location', '地点 Location'),
            ('camera', '相机 Camera'),
            ('lens', '镜头 Lens'),
            ('focal_length', '焦距 Focal'),
            ('aperture', '光圈 Aperture'),
            ('shutter_speed', '快门 Shutter'),
            ('iso', 'ISO'),
            ('date', '日期 Date'),
            ('note', '备注 Note'),
        ]
        
        for key, label in field_labels:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setFixedWidth(90)
            lbl.setStyleSheet('font-size: 11px; color: #9A9AA2;')
            edit = QLineEdit()
            edit.setPlaceholderText('(自动读取)')
            edit.setStyleSheet("")
            edit.textChanged.connect(lambda v, e=edit: self.params_changed.emit())
            row.addWidget(lbl)
            row.addWidget(edit, 1)
            exif_layout.addLayout(row)
            self.exif_fields[key] = edit
        
        layout.addWidget(exif_group)
        
        # --- Border Parameters ---
        border_group = QGroupBox('边框参数')
        border_group.setFont(QFont('Segoe UI', 10, QFont.Bold))
        border_layout = QVBoxLayout(border_group)
        border_layout.setSpacing(4)
        
        # Background color
        bg_row = QHBoxLayout()
        bg_row.addWidget(QLabel('背景色'))
        self.bg_color_btn = QPushButton()
        self.bg_color_btn.setFixedSize(28, 28)
        self.bg_color_btn.setStyleSheet(
            f'background-color: rgb{self._bg_color}; border: 1px solid #3A3A3C; border-radius: 8px;'
        )
        self.bg_color_btn.clicked.connect(self._on_bg_color)
        bg_row.addWidget(self.bg_color_btn)
        bg_row.addStretch()
        border_layout.addLayout(bg_row)
        
        # Margin sliders
        self.margin_sliders = {}
        slider_configs = [
            ('margin_top', '顶部留白', 0, 300, 60),
            ('margin_side', '左右留白', 0, 300, 80),
            ('margin_bottom', '底部留白', 0, 400, 120),
            ('image_corner_radius', '图片圆角', 0, 100, 0),
        ]
        
        for key, label, mn, mx, default in slider_configs:
            border_layout.addWidget(self._make_slider(key, label, mn, mx, default))
        
        # Shadow checkbox
        self.shadow_check = QCheckBox('图片阴影')
        self.shadow_check.stateChanged.connect(lambda v: self.params_changed.emit())
        border_layout.addWidget(self.shadow_check)
        
        # Font settings
        font_label = QLabel('字体设置')
        font_label.setStyleSheet('font-weight: bold; margin-top: 8px;')
        border_layout.addWidget(font_label)
        
        self.font_sliders = {}
        font_configs = [
            ('font_size', '字体大小', 8, 48, 18),
        ]
        for key, label, mn, mx, default in font_configs:
            border_layout.addWidget(self._make_slider(key, label, mn, mx, default))
        
        # Font color
        fc_row = QHBoxLayout()
        fc_row.addWidget(QLabel('字体颜色'))
        self.font_color_btn = QPushButton()
        self.font_color_btn.setFixedSize(28, 28)
        self.font_color_btn.setStyleSheet(
            f'background-color: rgb{self._font_color}; border: 1px solid #3A3A3C; border-radius: 8px;'
        )
        self.font_color_btn.clicked.connect(self._on_font_color)
        fc_row.addWidget(self.font_color_btn)
        fc_row.addStretch()
        border_layout.addLayout(fc_row)
        
        # Font weight
        self.font_bold_check = QCheckBox('粗体')
        self.font_bold_check.stateChanged.connect(lambda v: self.params_changed.emit())
        border_layout.addWidget(self.font_bold_check)
        
        # Text alignment
        self.text_align_combo = self._make_standalone_combo(
            'text_align', '文字对齐', ['left', 'center', 'right'],
            ['左对齐', '居中', '右对齐']
        )
        border_layout.addWidget(self.text_align_combo)

        # Brand logo
        logo_label = QLabel('品牌 Logo')
        logo_label.setStyleSheet('font-weight: bold; margin-top: 8px; color: #F2F2F7;')
        border_layout.addWidget(logo_label)

        self.logo_check = QCheckBox('自动显示品牌 Logo')
        self.logo_check.setChecked(True)
        self.logo_check.stateChanged.connect(lambda v: self.params_changed.emit())
        border_layout.addWidget(self.logo_check)

        border_layout.addWidget(self._make_slider('logo_size', 'Logo 大小', 40, 180, 90))

        self.logo_position_combo = self._make_standalone_combo(
            'logo_position', 'Logo 位置',
            ['bottom_right', 'bottom_left', 'top_right', 'top_left'],
            ['右下', '左下', '右上', '左上']
        )
        border_layout.addWidget(self.logo_position_combo)

        qr_label = QLabel('GPS 二维码')
        qr_label.setStyleSheet('font-weight: bold; margin-top: 8px; color: #F2F2F7;')
        border_layout.addWidget(qr_label)

        self.qr_check = QCheckBox('有 GPS 时显示地图二维码')
        self.qr_check.setChecked(True)
        self.qr_check.stateChanged.connect(lambda v: self.params_changed.emit())
        border_layout.addWidget(self.qr_check)

        border_layout.addWidget(self._make_slider('qr_size', '二维码大小', 40, 180, 86))

        self.qr_position_combo = self._make_standalone_combo(
            'qr_position', '二维码位置',
            ['bottom_left', 'bottom_right', 'top_left', 'top_right'],
            ['左下', '右下', '左上', '右上']
        )
        border_layout.addWidget(self.qr_position_combo)

        self.map_provider_combo = self._make_standalone_combo(
            'map_provider', '地图服务',
            ['apple', 'google', 'geo'],
            ['Apple Maps', 'Google Maps', '通用 geo']
        )
        border_layout.addWidget(self.map_provider_combo)
        
        layout.addWidget(border_group)
        
        # --- Export Settings ---
        export_group = QGroupBox('导出设置')
        export_group.setFont(QFont('Segoe UI', 10, QFont.Bold))
        export_layout = QVBoxLayout(export_group)
        
        self.format_combo = self._make_standalone_combo(
            'export_format', '格式', ['JPEG', 'PNG'], ['JPG', 'PNG']
        )
        export_layout.addWidget(self.format_combo)
        
        self.resolution_combo = self._make_standalone_combo(
            'export_resolution', '分辨率', 
            ['1080px long edge', '2048px long edge', '3000px long edge', 'Original high resolution'],
            ['1080px 长边', '2048px 长边', '3000px 长边', '原始高清']
        )
        export_layout.addWidget(self.resolution_combo)
        
        layout.addWidget(export_group)
        
        layout.addStretch()
        
        scroll.setWidget(container)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
        # Connect combo signals (wrap in lambda to discard the value argument)
        self._template_combo.currentTextChanged.connect(lambda v: self.params_changed.emit())
        self._ratio_combo.currentTextChanged.connect(lambda v: self.params_changed.emit())
        # Text alignment combo needs to trigger preview refresh
        self.text_align_combo.findChild(QComboBox).currentTextChanged.connect(
            lambda v: self.params_changed.emit()
        )
        self.logo_position_combo.findChild(QComboBox).currentTextChanged.connect(
            lambda v: self.params_changed.emit()
        )
        self.qr_position_combo.findChild(QComboBox).currentTextChanged.connect(
            lambda v: self.params_changed.emit()
        )
        self.map_provider_combo.findChild(QComboBox).currentTextChanged.connect(
            lambda v: self.params_changed.emit()
        )
        # Export format & resolution combos
        fmt_combo = self.format_combo.findChild(QComboBox)
        fmt_combo.currentTextChanged.connect(
            lambda v: self.export_format_changed.emit(v)
        )
        res_combo = self.resolution_combo.findChild(QComboBox)
        res_combo.currentTextChanged.connect(
            lambda v: self._on_resolution_changed(v)
        )
    
    def _make_group(self, title: str, widgets: list) -> QGroupBox:
        group = QGroupBox(title)
        group.setFont(QFont('Segoe UI', 10, QFont.Bold))
        glayout = QVBoxLayout(group)
        glayout.setSpacing(4)
        for w in widgets:
            glayout.addWidget(w)
        return group
    
    def _make_combo(self, key: str, label: str, values: list, display: list = None) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label)
        lbl.setFixedWidth(40)
        lbl.setStyleSheet('font-size: 11px; color: #9A9AA2;')
        combo = QComboBox()
        combo.addItems(display or values)
        combo.setStyleSheet("")
        layout.addWidget(lbl)
        layout.addWidget(combo, 1)
        
        setattr(self, f'_{key}_combo', combo)
        return w
    
    def _make_standalone_combo(self, key: str, label: str, values: list, display: list = None) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label)
        lbl.setFixedWidth(55)
        lbl.setStyleSheet('font-size: 11px; color: #9A9AA2;')
        combo = QComboBox()
        combo.addItems(display or values)
        combo.setStyleSheet("")
        layout.addWidget(lbl)
        layout.addWidget(combo, 1)
        return w
    
    def _make_slider(self, key: str, label: str, mn: int, mx: int, default: int) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 2, 0, 2)
        
        lbl = QLabel(label)
        lbl.setFixedWidth(70)
        lbl.setStyleSheet('font-size: 11px; color: #9A9AA2;')
        
        slider = QSlider(Qt.Horizontal)
        slider.setRange(mn, mx)
        slider.setValue(default)
        slider.setStyleSheet("")
        slider.valueChanged.connect(lambda v: self.params_changed.emit())
        
        val_lbl = QLabel(str(default))
        val_lbl.setFixedWidth(36)
        val_lbl.setAlignment(Qt.AlignRight)
        val_lbl.setStyleSheet('font-size: 11px; color: #C7C7CC;')
        slider.valueChanged.connect(lambda v: val_lbl.setText(str(v)))
        
        layout.addWidget(lbl)
        layout.addWidget(slider, 1)
        layout.addWidget(val_lbl)
        
        self.margin_sliders[key] = slider
        return w
    
    def _on_bg_color(self):
        color = QColorDialog.getColor(QColor(*self._bg_color), self, '选择背景颜色')
        if color.isValid():
            self._bg_color = (color.red(), color.green(), color.blue())
            self.bg_color_btn.setStyleSheet(
                f'background-color: rgb{self._bg_color}; border: 1px solid #3A3A3C; border-radius: 8px;'
            )
            self.params_changed.emit()
    
    def _on_font_color(self):
        color = QColorDialog.getColor(QColor(*self._font_color), self, '选择字体颜色')
        if color.isValid():
            self._font_color = (color.red(), color.green(), color.blue())
            self.font_color_btn.setStyleSheet(
                f'background-color: rgb{self._font_color}; border: 1px solid #3A3A3C; border-radius: 8px;'
            )
            self.params_changed.emit()
    
    def _on_resolution_changed(self, value: str):
        resolution_map = {
            '1080px 长边': 1080,
            '2048px 长边': 2048,
            '3000px 长边': 3000,
            '原始高清': 0,
        }
        self.export_resolution_changed.emit(resolution_map.get(value, 2048))
    
    # --- Getters for all current values ---
    def get_template_key(self) -> str:
        display = self._template_combo.currentText()
        mapping = {
            'Museum White 美术馆白': 'museum_white',
            'Gallery Black 画廊黑': 'gallery_black',
            'Off-white Archive 档案卡': 'offwhite_archive',
            'Minimal Border 极简边框': 'minimal_border',
            'Vintage Postcard 复古明信片': 'contact_sheet',
        }
        return mapping.get(display, 'museum_white')
    
    def get_ratio_key(self) -> str:
        return self._ratio_combo.currentText()
    
    def get_bg_color(self) -> tuple:
        return self._bg_color
    
    def get_font_color(self) -> tuple:
        return self._font_color
    
    def get_margin(self, key: str) -> int:
        slider = self.margin_sliders.get(key)
        return slider.value() if slider else 0
    
    def get_shadow(self) -> bool:
        return self.shadow_check.isChecked()
    
    def get_font_size(self) -> int:
        slider = self.margin_sliders.get('font_size')
        return slider.value() if slider else 18
    
    def get_font_bold(self) -> bool:
        return self.font_bold_check.isChecked()
    
    def get_text_align(self) -> str:
        idx = self.text_align_combo.findChild(QComboBox).currentIndex()
        return ['left', 'center', 'right'][idx]

    def get_logo_enabled(self) -> bool:
        return self.logo_check.isChecked()

    def get_logo_size(self) -> int:
        slider = self.margin_sliders.get('logo_size')
        return slider.value() if slider else 90

    def get_logo_position(self) -> str:
        idx = self.logo_position_combo.findChild(QComboBox).currentIndex()
        return ['bottom_right', 'bottom_left', 'top_right', 'top_left'][idx]

    def get_qr_enabled(self) -> bool:
        return self.qr_check.isChecked()

    def get_qr_size(self) -> int:
        slider = self.margin_sliders.get('qr_size')
        return slider.value() if slider else 86

    def get_qr_position(self) -> str:
        idx = self.qr_position_combo.findChild(QComboBox).currentIndex()
        return ['bottom_left', 'bottom_right', 'top_left', 'top_right'][idx]

    def get_map_provider(self) -> str:
        idx = self.map_provider_combo.findChild(QComboBox).currentIndex()
        return ['apple', 'google', 'geo'][idx]
    
    def get_exif_field(self, key: str) -> str:
        edit = self.exif_fields.get(key)
        return edit.text() if edit else ''
    
    def set_exif_field(self, key: str, value: str, overwrite: bool = False):
        """Set an EXIF field from auto-read data."""
        edit = self.exif_fields.get(key)
        if edit and (overwrite or not edit.text()):
            edit.blockSignals(True)
            edit.setText(value or '')
            edit.blockSignals(False)
    
    def set_all_exif_fields(self, exif_data: dict, overwrite: bool = False):
        """Populate all EXIF fields from auto-read data."""
        for key in ['camera', 'lens', 'focal_length', 'aperture',
                     'shutter_speed', 'iso', 'date', 'location']:
            self.set_exif_field(key, exif_data.get(key, ''), overwrite=overwrite)
    
    def get_export_format(self) -> str:
        display = self.format_combo.findChild(QComboBox).currentText()
        return 'JPEG' if display == 'JPG' else display
    
    def get_export_resolution(self) -> int:
        resolution_map = {
            '1080px 长边': 1080,
            '2048px 长边': 2048,
            '3000px 长边': 3000,
            '原始高清': 0,
        }
        val = self.resolution_combo.findChild(QComboBox).currentText()
        return resolution_map.get(val, 2048)
