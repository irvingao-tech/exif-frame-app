"""Right panel controls with a Codex-like light interface."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QSlider,
    QPushButton, QScrollArea, QHBoxLayout, QCheckBox, QColorDialog,
    QFrame, QSizePolicy, QStyle, QStyleOptionSlider,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor


class TrackSlider(QSlider):
    """A horizontal slider that tracks from any click/drag point."""

    interaction_finished = Signal()

    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setTracking(True)
        self.setMouseTracking(True)
        self.setPageStep(1)
        self._dragging = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._set_value_from_pos(event.position().x())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self._set_value_from_pos(event.position().x())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            self._set_value_from_pos(event.position().x())
            self.interaction_finished.emit()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _set_value_from_pos(self, x_pos: float):
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        groove = self.style().subControlRect(
            QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self
        )
        handle = self.style().subControlRect(
            QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self
        )
        slider_min = groove.x()
        slider_max = groove.right() - handle.width() + 1
        span = max(slider_max - slider_min, 1)
        pos = max(slider_min, min(int(x_pos) - handle.width() // 2, slider_max))
        value = QStyle.sliderValueFromPosition(
            self.minimum(), self.maximum(), pos - slider_min, span, opt.upsideDown
        )
        self.setValue(value)


class ControlsPanel(QWidget):
    params_changed = Signal()
    export_format_changed = Signal(str)
    export_resolution_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('ControlsPanel')
        self.setMinimumWidth(280)
        self.setMaximumWidth(360)
        self._bg_color = (250, 249, 245)
        self._font_color = (55, 55, 58)
        self._header_color = (74, 58, 42)
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setObjectName('ControlsScroll')
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content.setObjectName('ControlsContent')
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 12)
        layout.setSpacing(8)

        layout.addWidget(self._section('Template', [
            self._batch_toggle(),
            self._combo('template', [
                ('museum_white', 'Museum White'),
                ('gallery_black', 'Gallery Black'),
                ('offwhite_archive', 'Off-white Archive'),
                ('minimal_border', 'Minimal Border'),
                ('contact_sheet', 'Vintage Postcard'),
                ('color_reversal_film', 'Color Reversal Film'),
            ], label='Style'),
            self._combo('ratio', [
                ('Original', 'Original'), ('1:1', 'Square 1:1'),
                ('4:5', 'Portrait 4:5'), ('3:4', 'Portrait 3:4'),
                ('16:9', 'Wide 16:9'), ('9:16', 'Story 9:16'),
                ('A4 Portrait', 'A4 Portrait'),
                ('A4 Landscape', 'A4 Landscape'),
            ], label='Canvas'),
            self._combo('preview_quality', [
                ('performance', 'Performance'),
                ('balanced', 'Balanced'),
                ('quality', 'Quality'),
                ('ultra', 'Ultra'),
            ], label='Preview Quality'),
        ]))

        self.exif_fields = {}
        exif_widgets = []
        for key, label, placeholder in [
            ('title', 'Title', 'Untitled frame'),
            ('location', 'Location', 'Location'),
            ('camera', 'Camera', 'Camera body'),
            ('lens', 'Lens', 'Lens name'),
            ('focal_length', 'Focal Length', '35mm'),
            ('aperture', 'Aperture', 'f/2.8'),
            ('shutter_speed', 'Shutter', '1/250s'),
            ('iso', 'ISO', 'ISO 100'),
            ('date', 'Date', '2026-05-15'),
        ]:
            edit = QLineEdit()
            edit.setPlaceholderText(placeholder)
            edit.textChanged.connect(lambda _v: self.params_changed.emit())
            self.exif_fields[key] = edit
            exif_widgets.append(self._field(label, edit))
        layout.addWidget(self._section('Metadata', exif_widgets))

        border_widgets = [
            self._color_row('Background', 'bg_swatch', self._bg_color, self._pick_bg),
            self._slider('margin_top', 'Top Margin', 0, 300, 60),
            self._slider('margin_side', 'Side Margin', 0, 300, 80),
            self._slider('margin_bottom', 'Bottom Margin', 0, 400, 120),
            self._slider('image_corner_radius', 'Image Radius', 0, 100, 0),
            self._slider('image_zoom', 'Photo Zoom', 100, 220, 100),
            self._slider('image_offset_x', 'Photo X', -100, 100, 0),
            self._slider('image_offset_y', 'Photo Y', -100, 100, 0),
        ]
        self.shadow_check = QCheckBox('Image shadow')
        self.shadow_check.stateChanged.connect(lambda _v: self.params_changed.emit())
        border_widgets.append(self.shadow_check)
        layout.addWidget(self._section('Frame', border_widgets))

        text_widgets = [
            self._slider('font_size', 'Text Size', 8, 48, 43),
            self._color_row('Text Color', 'fc_swatch', self._font_color, self._pick_font_color),
        ]
        self.bold_check = QCheckBox('Bold text')
        self.bold_check.stateChanged.connect(lambda _v: self.params_changed.emit())
        text_widgets.append(self.bold_check)
        text_widgets.append(self._combo('text_align', [
            ('left', 'Left'), ('center', 'Center'), ('right', 'Right'),
        ], label='Alignment'))
        layout.addWidget(self._section('Typography', text_widgets))

        header_edit = QLineEdit()
        header_edit.setPlaceholderText('CARTE POSTALE')
        header_edit.textChanged.connect(lambda _v: self.params_changed.emit())
        self.exif_fields['postcard_header'] = header_edit
        header_widgets = [
            self._field('Header Text', header_edit),
            self._slider('postcard_header_size', 'Header Size', 8, 56, 18),
            self._color_row('Header Color', 'hc_swatch', self._header_color, self._pick_header_color),
        ]
        self.header_bold_check = QCheckBox('Bold header')
        self.header_bold_check.setChecked(True)
        self.header_bold_check.stateChanged.connect(lambda _v: self.params_changed.emit())
        header_widgets.append(self.header_bold_check)
        layout.addWidget(self._section('Header Style', header_widgets))

        self.logo_check = QCheckBox('Show camera brand logo')
        self.logo_check.setChecked(True)
        self.logo_check.stateChanged.connect(lambda _v: self.params_changed.emit())

        self.qr_check = QCheckBox('Show GPS map QR')
        self.qr_check.setChecked(True)
        self.qr_check.stateChanged.connect(lambda _v: self.params_changed.emit())

        layout.addWidget(self._section('Logo & Map', [
            self.logo_check,
            self._slider('logo_size', 'Logo Size', 40, 180, 90),
            self._combo('logo_position', [
                ('bottom_right', 'Bottom Right'), ('bottom_left', 'Bottom Left'),
                ('top_right', 'Top Right'), ('top_left', 'Top Left'),
            ], label='Logo Position'),
            self.qr_check,
            self._slider('qr_size', 'QR Size', 40, 180, 86),
            self._combo('qr_position', [
                ('bottom_left', 'Bottom Left'), ('bottom_right', 'Bottom Right'),
                ('top_left', 'Top Left'), ('top_right', 'Top Right'),
            ], label='QR Position'),
            self._combo('map_provider', [
                ('apple', 'Apple Maps'), ('google', 'Google Maps'),
                ('geo', 'Universal geo link'),
            ], label='Map Link'),
        ]))

        layout.addWidget(self._section('Export', [
            self._combo('export_format', [
                ('JPEG', 'JPG'), ('PNG', 'PNG'),
            ], label='Format'),
            self._combo('export_resolution', [
                ('1080', '1080px long edge'),
                ('2048', '2048px long edge'),
                ('3000', '3000px long edge'),
                ('0', 'Original size'),
            ], label='Resolution'),
        ]))
        layout.addStretch()

        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        for name in ['template', 'ratio', 'preview_quality', 'text_align',
                     'logo_position', 'qr_position', 'map_provider']:
            getattr(self, f'_combo_{name}').currentTextChanged.connect(
                lambda _v: self.params_changed.emit())

        self._combo_export_format.currentIndexChanged.connect(
            lambda _idx: self.export_format_changed.emit(self._combo_val('export_format')))
        self._combo_export_resolution.currentIndexChanged.connect(
            lambda _idx: self._on_resolution())

        self._combo_ratio.setCurrentIndex(0)
        self._combo_preview_quality.setCurrentIndex(0)
        self._combo_export_resolution.setCurrentIndex(1)

    def _batch_toggle(self) -> QWidget:
        self.batch_check = QCheckBox('Batch edit mode')
        self.batch_check.setToolTip('Apply visual style changes to every imported photo.')
        self.batch_check.stateChanged.connect(lambda _v: self.params_changed.emit())
        return self.batch_check

    def _section(self, title: str, widgets: list[QWidget]) -> QWidget:
        section = QWidget()
        section.setObjectName('ControlSection')
        outer = QVBoxLayout(section)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(3)

        heading = QLabel(title)
        heading.setObjectName('SectionTitle')
        outer.addWidget(heading)

        card = QFrame()
        card.setObjectName('ControlCard')
        card.setFrameShape(QFrame.NoFrame)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(9, 7, 9, 7)
        card_layout.setSpacing(6)
        for widget in widgets:
            card_layout.addWidget(widget)
        outer.addWidget(card)
        return section

    def _field(self, label: str, edit: QLineEdit) -> QWidget:
        row = QWidget()
        lay = QVBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        lbl = QLabel(label)
        lbl.setObjectName('FieldLabel')
        lay.addWidget(lbl)
        lay.addWidget(edit)
        return row

    def _combo(self, name: str, items: list[tuple[str, str]], label: str = '') -> QWidget:
        row = QWidget()
        lay = QVBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        if label:
            lbl = QLabel(label)
            lbl.setObjectName('FieldLabel')
            lay.addWidget(lbl)
        cb = QComboBox()
        cb.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        cb.setMinimumContentsLength(16)
        cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        for val, disp in items:
            cb.addItem(disp, val)
        lay.addWidget(cb)
        setattr(self, f'_combo_{name}', cb)
        return row

    def _slider(self, name: str, label: str, mn: int, mx: int, dv: int) -> QWidget:
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)

        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label)
        lbl.setObjectName('FieldLabel')
        val = QLabel(str(dv))
        val.setObjectName('ValueLabel')
        val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        head.addWidget(lbl)
        head.addStretch()
        head.addWidget(val)

        slider = TrackSlider(Qt.Horizontal)
        slider.setRange(mn, mx)
        slider.setValue(dv)
        slider.valueChanged.connect(lambda v: val.setText(str(v)))
        slider.interaction_finished.connect(lambda: self.params_changed.emit())

        lay.addLayout(head)
        lay.addWidget(slider)

        if not hasattr(self, '_sliders'):
            self._sliders = {}
            self._slider_value_labels = {}
        self._sliders[name] = slider
        self._slider_value_labels[name] = val
        return box

    def _color_row(self, label: str, attr: str, color: tuple[int, int, int], slot) -> QWidget:
        row = QWidget()
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        lbl = QLabel(label)
        lbl.setObjectName('FieldLabel')
        btn = QPushButton()
        btn.setObjectName('ColorSwatch')
        btn.setFixedSize(22, 22)
        btn.setStyleSheet(f'QPushButton#ColorSwatch {{ background-color: rgb{color}; }}')
        btn.clicked.connect(slot)
        setattr(self, attr, btn)
        lay.addWidget(lbl)
        lay.addStretch()
        lay.addWidget(btn)
        return row

    def _pick_bg(self):
        c = QColorDialog.getColor(QColor(*self._bg_color), self, 'Background Color')
        if c.isValid():
            self._bg_color = (c.red(), c.green(), c.blue())
            self.bg_swatch.setStyleSheet(
                f'QPushButton#ColorSwatch {{ background-color: rgb{self._bg_color}; }}')
            self.params_changed.emit()

    def _pick_font_color(self):
        c = QColorDialog.getColor(QColor(*self._font_color), self, 'Text Color')
        if c.isValid():
            self._font_color = (c.red(), c.green(), c.blue())
            self.fc_swatch.setStyleSheet(
                f'QPushButton#ColorSwatch {{ background-color: rgb{self._font_color}; }}')
            self.params_changed.emit()

    def _pick_header_color(self):
        c = QColorDialog.getColor(QColor(*self._header_color), self, 'Header Color')
        if c.isValid():
            self._header_color = (c.red(), c.green(), c.blue())
            self.hc_swatch.setStyleSheet(
                f'QPushButton#ColorSwatch {{ background-color: rgb{self._header_color}; }}')
            self.params_changed.emit()

    def _on_resolution(self):
        self.export_resolution_changed.emit(int(self._combo_val('export_resolution') or 2048))

    def _set_combo_val(self, name: str, value: str):
        cb = getattr(self, f'_combo_{name}', None)
        if cb is None:
            return
        idx = cb.findData(value)
        if idx >= 0:
            cb.setCurrentIndex(idx)

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

    def get_batch_mode(self) -> bool:
        return self.batch_check.isChecked() if hasattr(self, 'batch_check') else False

    def get_preview_long_edge(self) -> int:
        quality = self._combo_val('preview_quality') or 'balanced'
        return {
            'performance': 800,
            'balanced': 1200,
            'quality': 1800,
            'ultra': 2600,
        }.get(quality, 1200)

    def get_bg_color(self) -> tuple:
        return self._bg_color

    def get_font_color(self) -> tuple:
        return self._font_color

    def get_margin(self, key: str) -> int:
        return self._slider_val(key, 0)

    def get_shadow(self) -> bool:
        return self.shadow_check.isChecked() if hasattr(self, 'shadow_check') else False

    def get_font_size(self) -> int:
        return self._slider_val('font_size', 43)

    def get_font_bold(self) -> bool:
        return self.bold_check.isChecked() if hasattr(self, 'bold_check') else False

    def get_text_align(self) -> str:
        return self._combo_val('text_align') or 'left'

    def get_postcard_header_size(self) -> int:
        return self._slider_val('postcard_header_size', 18)

    def get_postcard_header_color(self) -> tuple:
        return self._header_color

    def get_postcard_header_bold(self) -> bool:
        return self.header_bold_check.isChecked() if hasattr(self, 'header_bold_check') else True

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
        self.set_exif_field('postcard_header', 'CARTE POSTALE', overwrite=overwrite)
        for key in ['camera', 'lens', 'focal_length', 'aperture',
                    'shutter_speed', 'iso', 'date', 'location']:
            self.set_exif_field(key, exif_data.get(key, ''), overwrite=overwrite)

    def get_render_state(self) -> dict:
        return {
            'template': self._combo_val('template'),
            'ratio': self._combo_val('ratio'),
            'bg_color': self._bg_color,
            'font_color': self._font_color,
            'header_color': self._header_color,
            'margins': {
                name: slider.value()
                for name, slider in getattr(self, '_sliders', {}).items()
            },
            'shadow': self.get_shadow(),
            'bold': self.get_font_bold(),
            'header_bold': self.get_postcard_header_bold(),
            'text_align': self._combo_val('text_align'),
            'logo_enabled': self.get_logo_enabled(),
            'logo_position': self._combo_val('logo_position'),
            'qr_enabled': self.get_qr_enabled(),
            'qr_position': self._combo_val('qr_position'),
            'map_provider': self._combo_val('map_provider'),
        }

    def set_render_state(self, state: dict):
        if not state:
            return
        widgets = [
            getattr(self, f'_combo_{name}', None)
            for name in ['template', 'ratio', 'text_align', 'logo_position', 'qr_position', 'map_provider']
        ]
        widgets += list(getattr(self, '_sliders', {}).values())
        widgets += [
            self.shadow_check, self.bold_check, self.header_bold_check,
            self.logo_check, self.qr_check,
        ]
        for widget in [w for w in widgets if w is not None]:
            widget.blockSignals(True)
        try:
            self._set_combo_val('template', state.get('template'))
            self._set_combo_val('ratio', state.get('ratio'))
            self._set_combo_val('text_align', state.get('text_align'))
            self._set_combo_val('logo_position', state.get('logo_position'))
            self._set_combo_val('qr_position', state.get('qr_position'))
            self._set_combo_val('map_provider', state.get('map_provider'))
            self._bg_color = tuple(state.get('bg_color', self._bg_color))
            self._font_color = tuple(state.get('font_color', self._font_color))
            self._header_color = tuple(state.get('header_color', self._header_color))
            self.bg_swatch.setStyleSheet(
                f'QPushButton#ColorSwatch {{ background-color: rgb{self._bg_color}; }}')
            self.fc_swatch.setStyleSheet(
                f'QPushButton#ColorSwatch {{ background-color: rgb{self._font_color}; }}')
            self.hc_swatch.setStyleSheet(
                f'QPushButton#ColorSwatch {{ background-color: rgb{self._header_color}; }}')
            for name, value in state.get('margins', {}).items():
                slider = getattr(self, '_sliders', {}).get(name)
                if slider is not None:
                    slider.setValue(int(value))
                value_label = getattr(self, '_slider_value_labels', {}).get(name)
                if value_label is not None:
                    value_label.setText(str(int(value)))
            self.shadow_check.setChecked(bool(state.get('shadow', False)))
            self.bold_check.setChecked(bool(state.get('bold', False)))
            self.header_bold_check.setChecked(bool(state.get('header_bold', True)))
            self.logo_check.setChecked(bool(state.get('logo_enabled', True)))
            self.qr_check.setChecked(bool(state.get('qr_enabled', True)))
        finally:
            for widget in [w for w in widgets if w is not None]:
                widget.blockSignals(False)

    def get_metadata_state(self) -> dict:
        return {key: edit.text() for key, edit in self.exif_fields.items()}

    def set_metadata_state(self, state: dict):
        for key, edit in self.exif_fields.items():
            edit.blockSignals(True)
            edit.setText(state.get(key, ''))
            edit.blockSignals(False)

    def get_export_format(self) -> str:
        return self._combo_val('export_format') or 'JPEG'

    def get_export_resolution(self) -> int:
        return int(self._combo_val('export_resolution') or 2048)
