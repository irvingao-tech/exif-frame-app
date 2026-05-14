"""
Base Template class for EXIF Frame Card templates.
Each template defines how to render the final framed image.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from src.core.logo_registry import detect_brand, find_logo_path

DEFAULT_BG_COLOR = (250, 249, 245)
DEFAULT_FONT_COLOR = (80, 80, 80)


@dataclass
class RenderParams:
    """All configurable rendering parameters."""
    # Canvas ratio (width, height) — e.g. (4, 5) for 4:5
    ratio: Tuple[int, int] = (4, 5)
    # Target long edge in pixels
    target_long_edge: int = 2048
    # Background color
    bg_color: Tuple[int, int, int] = (250, 249, 245)
    # Border/margin in pixels (relative to target size)
    border_width: int = 0
    margin_top: int = 60
    margin_side: int = 80
    margin_bottom: int = 120
    # Image styling
    image_corner_radius: int = 0
    image_shadow: bool = False
    # Text styling
    font_size: int = 18
    font_color: Tuple[int, int, int] = (80, 80, 80)
    font_bold: bool = False
    text_align: str = 'left'  # 'left', 'center', 'right'
    # Brand logo styling
    logo_enabled: bool = False
    logo_size: int = 90
    logo_position: str = 'bottom_right'
    # GPS QR code styling
    qr_enabled: bool = True
    qr_size: int = 86
    qr_position: str = 'bottom_left'
    map_provider: str = 'apple'
    # EXIF override text fields
    title: str = ''
    location: str = ''
    camera: str = ''
    lens: str = ''
    focal_length: str = ''
    aperture: str = ''
    shutter_speed: str = ''
    iso: str = ''
    date: str = ''
    note: str = ''


@dataclass
class ExifSource:
    """Source EXIF data from file reader."""
    camera: str = ''
    lens: str = ''
    focal_length: str = ''
    focal_length_35mm: str = ''
    aperture: str = ''
    shutter_speed: str = ''
    iso: str = ''
    date: str = ''
    location: str = ''
    color_space: str = ''
    image_width: int = 0
    image_height: int = 0
    has_gps: bool = False
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    map_url: str = ''


def get_merged_exif(exif: ExifSource, params: RenderParams) -> dict:
    """Merge auto-read EXIF with user overrides."""
    return {
        'title': params.title or '',
        'location': params.location or exif.location,
        'camera': params.camera or exif.camera,
        'lens': params.lens or exif.lens,
        'focal_length': params.focal_length or exif.focal_length,
        'aperture': params.aperture or exif.aperture,
        'shutter_speed': params.shutter_speed or exif.shutter_speed,
        'iso': params.iso or exif.iso,
        'date': params.date or exif.date,
        'note': params.note or '',
        'has_gps': exif.has_gps,
        'gps_latitude': exif.gps_latitude,
        'gps_longitude': exif.gps_longitude,
        'map_url': exif.map_url,
    }


def calculate_canvas(
    img_w: int, img_h: int, ratio: Tuple[int, int], target_long_edge: int
) -> Tuple[int, int, float]:
    """
    Calculate canvas dimensions and scale factor.
    
    Returns (canvas_w, canvas_h, scale) where scale is the factor
    to resize the image to fit within the canvas (maintaining aspect ratio).
    """
    ratio_w, ratio_h = ratio
    
    # Determine the long edge of the canvas based on target
    if ratio_w >= ratio_h:
        canvas_w = target_long_edge
        canvas_h = int(target_long_edge * ratio_h / ratio_w)
    else:
        canvas_h = target_long_edge
        canvas_w = int(target_long_edge * ratio_w / ratio_h)
    
    # Calculate scale to fit image within canvas (with margins accounted for)
    # Reserve space for margins — roughly
    usable_w = canvas_w * 0.85
    usable_h = canvas_h * 0.75
    
    scale_w = usable_w / img_w if img_w > 0 else 1
    scale_h = usable_h / img_h if img_h > 0 else 1
    scale = min(scale_w, scale_h, 1.0)
    
    return canvas_w, canvas_h, scale


def draw_rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int, int, int],
    radius: int,
    fill=None,
    outline=None,
):
    """Draw a rounded rectangle on an ImageDraw."""
    if radius <= 0:
        draw.rectangle(xy, fill=fill, outline=outline)
        return
    
    x1, y1, x2, y2 = xy
    r = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
    
    # Use PIL's rounded_rectangle if available (Pillow >= 9.2)
    if hasattr(draw, 'rounded_rectangle'):
        draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline)
    else:
        draw.rectangle(xy, fill=fill, outline=outline)


def draw_shadow(
    base: Image.Image,
    img_box: Tuple[int, int, int, int],
    radius: int = 0,
    offset: int = 8,
    blur: int = 20,
    alpha: int = 60,
) -> Image.Image:
    """Draw a drop shadow behind an image area. Returns modified image."""
    import math
    
    x1, y1, x2, y2 = img_box
    
    # Create shadow layer
    shadow = Image.new('RGBA', base.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    
    # Draw multiple rectangles with decreasing alpha for blur effect
    steps = blur
    for i in range(steps):
        a = int(alpha * (1 - i / steps) * (1 - i / steps))
        expand = offset + i
        sx1 = x1 - expand
        sy1 = y1 - expand
        sx2 = x2 + expand
        sy2 = y2 + expand
        sr = radius + expand if radius > 0 else expand
        
        shadow_temp = Image.new('RGBA', base.size, (0, 0, 0, 0))
        stemp_draw = ImageDraw.Draw(shadow_temp)
        draw_rounded_rect(stemp_draw, (sx1, sy1, sx2, sy2), sr, fill=(0, 0, 0, a))
        shadow = Image.alpha_composite(shadow, shadow_temp)
    
    # Composite shadow onto base
    return Image.alpha_composite(base.convert('RGBA'), shadow)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a clean sans-serif font. Falls back gracefully."""
    font_paths = [
        # Windows
        'C:/Windows/Fonts/segoeui.ttf',
        'C:/Windows/Fonts/segoeuib.ttf',
        'C:/Windows/Fonts/seguiemj.ttf',
        'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/arialbd.ttf',
        # macOS
        '/System/Library/Fonts/SFNSDisplay.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
        # Linux
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ]
    
    # If bold, prefer bold variants
    if bold:
        bold_paths = [
            'C:/Windows/Fonts/segoeuib.ttf',
            'C:/Windows/Fonts/arialbd.ttf',
        ]
        font_paths = bold_paths + font_paths
    
    for fp in font_paths:
        try:
            return ImageFont.truetype(fp, size)
        except (IOError, OSError):
            continue
    
    # Ultimate fallback
    try:
        return ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', size)
    except Exception:
        return ImageFont.load_default()


def tint_monochrome_logo(logo: Image.Image, color: Tuple[int, int, int]) -> Image.Image:
    """Tint dark logo artwork while preserving colored brand accents."""
    rgba = logo.convert('RGBA')
    pixels = rgba.getdata()
    visible = [p for p in pixels if p[3] > 8]
    if not visible:
        return rgba

    is_monochrome = all(max(p[:3]) - min(p[:3]) <= 8 for p in visible)
    if not is_monochrome:
        recolored = []
        for r, g, b, a in pixels:
            if a > 8 and max(r, g, b) < 48:
                recolored.append((*color, a))
            else:
                recolored.append((r, g, b, a))
        rgba.putdata(recolored)
        return rgba

    tinted = Image.new('RGBA', rgba.size, (*color, 0))
    tinted.putalpha(rgba.getchannel('A'))
    return tinted


def minimum_safe_margins(
    canvas_w: int,
    canvas_h: int,
    params: RenderParams,
    text_lines: int = 1,
) -> tuple[int, int]:
    """Return minimum top/bottom space needed to avoid clipping text or logo."""
    scale_base = max(canvas_w, canvas_h) / 2048
    text_h = int(max(params.font_size, 10) * max(text_lines, 1) * 1.7) + 18
    logo_h = int(params.logo_size * scale_base) + 18 if params.logo_enabled else 0
    qr_h = int(params.qr_size * scale_base) + 18 if params.qr_enabled else 0

    min_top = 0
    min_bottom = text_h
    if params.logo_enabled and (params.logo_position or '').startswith('top'):
        min_top = logo_h
    elif params.logo_enabled:
        min_bottom = max(min_bottom, logo_h)
    if params.qr_enabled and (params.qr_position or '').startswith('top'):
        min_top = max(min_top, qr_h)
    elif params.qr_enabled:
        min_bottom = max(min_bottom, qr_h)

    return min_top, min_bottom


def template_colors(
    params: RenderParams,
    default_bg: Tuple[int, int, int],
    default_font: Tuple[int, int, int],
) -> tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """Use template colors unless the user has chosen custom colors."""
    bg = default_bg if params.bg_color == DEFAULT_BG_COLOR else params.bg_color
    font = default_font if params.font_color == DEFAULT_FONT_COLOR else params.font_color
    return bg, font


def mix_color(a: Tuple[int, int, int], b: Tuple[int, int, int], amount: float) -> Tuple[int, int, int]:
    """Blend two RGB colors."""
    amount = max(0.0, min(1.0, amount))
    return tuple(int(a[i] * (1 - amount) + b[i] * amount) for i in range(3))


def make_map_url(lat: float, lon: float, provider: str = 'apple') -> str:
    """Build a map URL from decimal coordinates."""
    provider = (provider or 'apple').lower()
    if provider == 'google':
        return f'https://maps.google.com/?q={lat:.6f},{lon:.6f}'
    if provider == 'geo':
        return f'geo:{lat:.6f},{lon:.6f}?q={lat:.6f},{lon:.6f}'
    return f'https://maps.apple.com/?ll={lat:.6f},{lon:.6f}&q=Photo%20Location'


def make_qr_image(data: str, fill: Tuple[int, int, int], back: Tuple[int, int, int]) -> Optional[Image.Image]:
    """Create a QR image if the optional qrcode dependency is available."""
    if not data:
        return None
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color=fill, back_color=back).convert('RGB')
        return img.convert('RGBA')
    except Exception:
        return None


class BaseTemplate(ABC):
    """Abstract base class for all frame templates."""
    
    name: str = 'Base'
    description: str = ''
    
    @abstractmethod
    def render(
        self,
        image: Image.Image,
        exif: ExifSource,
        params: RenderParams,
    ) -> Image.Image:
        """
        Render the framed image.
        
        Args:
            image: Source PIL Image (RGB)
            exif: Extracted EXIF data
            params: Rendering parameters
        
        Returns:
            Rendered PIL Image (RGB)
        """
        pass
    
    def _build_exif_line(self, merged: dict) -> str:
        """Build a single-line EXIF summary."""
        parts = []
        for key in ['camera', 'lens', 'focal_length', 'aperture', 'shutter_speed', 'iso']:
            val = merged.get(key, '')
            if val:
                # Avoid duplicate camera in lens
                if key == 'lens' and merged.get('camera') and str(merged['camera']) in str(val):
                    continue
                parts.append(val)
        if merged.get('location'):
            parts.append(merged['location'])
        if merged.get('date'):
            parts.append(merged['date'])
        return ' · '.join(parts)
    
    def _draw_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        x: int,
        y: int,
        max_width: int,
        font: ImageFont.FreeTypeFont,
        fill: Tuple[int, int, int],
        align: str = 'left',
    ):
        """Draw text with alignment support."""
        if not text:
            return
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        
        if align == 'center':
            x = x - text_w // 2
        elif align == 'right':
            x = x - text_w
        
        draw.text((x, y), text, fill=fill, font=font)

    def _fit_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        max_width: int,
        size: int,
        bold: bool = False,
        min_size: int = 8,
    ) -> tuple[str, ImageFont.FreeTypeFont]:
        """Fit text inside max_width by shrinking, then ellipsizing."""
        if not text:
            return '', load_font(max(min_size, size), bold)

        max_width = max(1, int(max_width))
        for font_size in range(max(size, min_size), min_size - 1, -1):
            font = load_font(font_size, bold)
            bbox = draw.textbbox((0, 0), text, font=font)
            if bbox[2] - bbox[0] <= max_width:
                return text, font

        font = load_font(min_size, bold)
        ellipsis = '...'
        fitted = text
        while fitted:
            candidate = fitted.rstrip() + ellipsis
            bbox = draw.textbbox((0, 0), candidate, font=font)
            if bbox[2] - bbox[0] <= max_width:
                return candidate, font
            fitted = fitted[:-1]
        return ellipsis, font

    def _draw_fitted_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        x: int,
        y: int,
        max_width: int,
        size: int,
        fill: Tuple[int, int, int],
        bold: bool = False,
        align: str = 'left',
        min_size: int = 8,
    ) -> int:
        """Draw one text line constrained to a fixed horizontal area."""
        fitted, font = self._fit_text(draw, text, max_width, size, bold, min_size)
        if not fitted:
            return 0

        bbox = draw.textbbox((0, 0), fitted, font=font)
        text_w = bbox[2] - bbox[0]
        if align == 'center':
            tx = x + max(0, (max_width - text_w) // 2)
        elif align == 'right':
            tx = x + max(0, max_width - text_w)
        else:
            tx = x
        draw.text((tx, y), fitted, fill=fill, font=font)
        return bbox[3] - bbox[1]

    def _get_brand_logo_artwork(
        self,
        canvas: Image.Image,
        merged: dict,
        params: RenderParams,
        max_width: int,
        max_height: int,
    ) -> Optional[dict]:
        """Prepare logo image or fallback wordmark at a bounded size."""
        if not params.logo_enabled:
            return None

        brand = detect_brand(merged.get('camera', ''), merged.get('lens', ''))
        if not brand:
            return None

        canvas_w, canvas_h = canvas.size
        scale_base = max(canvas_w, canvas_h) / 2048
        target_h = max(18, int(params.logo_size * scale_base))
        target_h = min(target_h, max(18, int(max_height)))
        max_width = max(1, int(max_width))

        logo_path = find_logo_path(brand['key'])
        if logo_path:
            try:
                logo_img = Image.open(logo_path).convert('RGBA')
                ratio = min(
                    target_h / max(logo_img.height, 1),
                    max_width / max(logo_img.width, 1),
                )
                logo_img = logo_img.resize(
                    (
                        max(1, int(logo_img.width * ratio)),
                        max(1, int(logo_img.height * ratio)),
                    ),
                    Image.LANCZOS,
                )
                logo_img = tint_monochrome_logo(logo_img, params.font_color)
                return {
                    'brand': brand,
                    'image': logo_img,
                    'width': logo_img.width,
                    'height': logo_img.height,
                }
            except Exception:
                pass

        draw = ImageDraw.Draw(canvas)
        fitted, font = self._fit_text(draw, brand['label'], max_width, target_h, True, 10)
        bbox = draw.textbbox((0, 0), fitted, font=font)
        return {
            'brand': brand,
            'text': fitted,
            'font': font,
            'width': bbox[2] - bbox[0],
            'height': bbox[3] - bbox[1],
        }

    def _get_logo_box(
        self,
        canvas: Image.Image,
        merged: dict,
        params: RenderParams,
        image_box: Tuple[int, int, int, int],
        margin_side: int,
        margin_top: int,
        margin_bottom: int,
    ) -> Optional[dict]:
        """Calculate a logo box that avoids the photo."""
        canvas_w, canvas_h = canvas.size
        safe_gap = max(8, int(canvas_h * 0.012))
        position = params.logo_position or 'bottom_right'

        if position.startswith('top'):
            area_top = safe_gap
            area_bottom = max(area_top, image_box[1] - safe_gap)
        else:
            area_top = min(canvas_h - safe_gap, image_box[3] + safe_gap)
            area_bottom = canvas_h - safe_gap

        area_h = area_bottom - area_top
        if area_h < 18 and position.startswith('top'):
            area_top = min(canvas_h - safe_gap, image_box[3] + safe_gap)
            area_bottom = canvas_h - safe_gap
            area_h = area_bottom - area_top
        if area_h < 18:
            return None

        max_logo_w = max(40, canvas_w - 2 * max(8, margin_side))
        artwork = self._get_brand_logo_artwork(
            canvas, merged, params, max_logo_w, area_h
        )
        if not artwork:
            return None

        logo_w = artwork['width']
        logo_h = artwork['height']
        if position.endswith('right'):
            x = canvas_w - margin_side - logo_w
        else:
            x = margin_side
        x = max(8, min(x, canvas_w - logo_w - 8))

        y = area_top + max(0, (area_h - logo_h) // 2)
        y = max(8, min(y, canvas_h - logo_h - 8))

        artwork.update({'x': x, 'y': y})
        return artwork

    def _text_area_avoiding_logo(
        self,
        fallback_x: int,
        y: int,
        max_width: int,
        line_height: int,
        logo_box: Optional[dict],
        gap: int = 16,
    ) -> tuple[int, int]:
        """Shrink a text area when it shares vertical space with a logo."""
        if not logo_box:
            return fallback_x, max_width

        text_top = y
        text_bottom = y + max(1, line_height)
        logo_top = logo_box['y']
        logo_bottom = logo_box['y'] + logo_box['height']
        if text_bottom < logo_top or text_top > logo_bottom:
            return fallback_x, max_width

        text_right = fallback_x + max_width
        logo_left = logo_box['x']
        logo_right = logo_box['x'] + logo_box['width']

        if logo_left >= fallback_x:
            return fallback_x, max(1, logo_left - fallback_x - gap)
        if logo_right <= text_right:
            new_x = logo_right + gap
            return new_x, max(1, text_right - new_x)
        return fallback_x, max_width

    def _text_area_avoiding_boxes(
        self,
        fallback_x: int,
        y: int,
        max_width: int,
        line_height: int,
        boxes: list,
        gap: int = 16,
    ) -> tuple[int, int]:
        """Shrink a text area when it shares vertical space with positioned art."""
        x = fallback_x
        width = max_width
        for box in [b for b in boxes if b]:
            x, width = self._text_area_avoiding_logo(x, y, width, line_height, box, gap)
        return x, width

    def _get_gps_qr_box(
        self,
        canvas: Image.Image,
        merged: dict,
        params: RenderParams,
        image_box: Tuple[int, int, int, int],
        margin_side: int,
        margin_top: int,
        margin_bottom: int,
        bg_color: Tuple[int, int, int],
    ) -> Optional[dict]:
        """Calculate a QR code box for GPS map links."""
        if not params.qr_enabled or not merged.get('has_gps'):
            return None

        map_url = merged.get('map_url')
        if not map_url and merged.get('gps_latitude') is not None and merged.get('gps_longitude') is not None:
            map_url = make_map_url(
                float(merged['gps_latitude']),
                float(merged['gps_longitude']),
                params.map_provider,
            )
        if not map_url:
            return None

        canvas_w, canvas_h = canvas.size
        scale_base = max(canvas_w, canvas_h) / 2048
        safe_gap = max(8, int(canvas_h * 0.012))
        position = params.qr_position or 'bottom_left'

        if position.startswith('top'):
            area_top = safe_gap
            area_bottom = max(area_top, image_box[1] - safe_gap)
        else:
            area_top = min(canvas_h - safe_gap, image_box[3] + safe_gap)
            area_bottom = canvas_h - safe_gap

        area_h = area_bottom - area_top
        if area_h < 24 and position.startswith('top'):
            area_top = min(canvas_h - safe_gap, image_box[3] + safe_gap)
            area_bottom = canvas_h - safe_gap
            area_h = area_bottom - area_top
        if area_h < 24:
            return None

        readable_min = 72 if max(canvas_w, canvas_h) >= 700 else 56
        size = max(readable_min, int(params.qr_size * scale_base))
        size = min(size, max(24, area_h), max(24, canvas_w - 2 * max(8, margin_side)))
        qr_img = make_qr_image(map_url, fill=params.font_color, back=bg_color)
        if qr_img is None:
            return None

        qr_img = qr_img.resize((size, size), Image.Resampling.NEAREST)
        if position.endswith('right'):
            x = canvas_w - margin_side - size
        else:
            x = margin_side
        x = max(8, min(x, canvas_w - size - 8))
        y = area_top + max(0, (area_h - size) // 2)
        y = max(8, min(y, canvas_h - size - 8))

        return {
            'image': qr_img,
            'url': map_url,
            'x': x,
            'y': y,
            'width': size,
            'height': size,
        }

    def _draw_gps_qr(
        self,
        canvas: Image.Image,
        merged: dict,
        params: RenderParams,
        image_box: Tuple[int, int, int, int],
        margin_side: int,
        margin_top: int,
        margin_bottom: int,
        bg_color: Tuple[int, int, int],
    ):
        """Draw GPS QR code if a map URL is available."""
        qr_box = self._get_gps_qr_box(
            canvas, merged, params, image_box, margin_side, margin_top, margin_bottom, bg_color
        )
        if not qr_box:
            return None
        canvas.paste(qr_box['image'], (qr_box['x'], qr_box['y']), qr_box['image'])
        return qr_box

    def _draw_brand_logo(
        self,
        canvas: Image.Image,
        merged: dict,
        params: RenderParams,
        image_box: Tuple[int, int, int, int],
        margin_side: int,
        margin_top: int,
        margin_bottom: int,
    ):
        """Draw a detected camera/lens brand logo or wordmark."""
        logo = self._get_logo_box(
            canvas, merged, params, image_box, margin_side, margin_top, margin_bottom
        )
        if not logo:
            return None

        x = logo['x']
        y = logo['y']
        if logo.get('image'):
            canvas.paste(logo['image'], (x, y), logo['image'])
            return logo

        draw = ImageDraw.Draw(canvas)
        draw.text((x, y), logo['text'], fill=params.font_color, font=logo['font'])
        return logo
