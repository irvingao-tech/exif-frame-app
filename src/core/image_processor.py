"""
Image Processor
Coordinates EXIF reading, template selection, and rendering.
"""

import logging
from typing import Optional, Dict, Any

from PIL import Image

from .exif_reader import read_exif
from src.templates.base import RenderParams, ExifSource
from src.templates.museum_white import MuseumWhiteTemplate
from src.templates.gallery_black import GalleryBlackTemplate
from src.templates.offwhite_archive import OffWhiteArchiveTemplate
from src.templates.minimal_border import MinimalBorderTemplate
from src.templates.contact_sheet import ContactSheetTemplate
from src.templates.color_reversal_film import ColorReversalFilmTemplate
from src.templates.full_width_info_bar import FullWidthInfoBarTemplate

logger = logging.getLogger(__name__)
PREVIEW_LAYOUT_LONG_EDGE = 2048

# Template registry — easy to extend
TEMPLATES = {
    'museum_white': MuseumWhiteTemplate(),
    'gallery_black': GalleryBlackTemplate(),
    'offwhite_archive': OffWhiteArchiveTemplate(),
    'minimal_border': MinimalBorderTemplate(),
    'contact_sheet': ContactSheetTemplate(),
    'color_reversal_film': ColorReversalFilmTemplate(),
    'full_width_info_bar': FullWidthInfoBarTemplate(),
}

# Aspect ratio presets
RATIOS = {
    'Original': None,
    '1:1': (1, 1),
    '4:5': (4, 5),
    '3:4': (3, 4),
    '16:9': (16, 9),
    '9:16': (9, 16),
    'A4 Portrait': (210, 297),
    'A4 Landscape': (297, 210),
}


def load_image(filepath: str, max_long_edge: int = 0) -> Optional[Image.Image]:
    """Load an image file, convert to RGB."""
    try:
        img = Image.open(filepath)
        if max_long_edge > 0:
            try:
                img.draft('RGB', (max_long_edge, max_long_edge))
            except Exception:
                pass
            img.thumbnail((max_long_edge, max_long_edge), Image.LANCZOS)
            img = img.copy()
        # Convert to RGB (handle RGBA, P, etc.)
        if img.mode in ('RGBA', 'P', 'LA'):
            # Create white background for transparency
            if img.mode == 'P':
                img = img.convert('RGBA')
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA':
                background.paste(img, mask=img.split()[3])
            else:
                background.paste(img)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        return img
    except Exception as e:
        logger.error(f'Failed to load image {filepath}: {e}')
        return None


def process_image(
    filepath: str,
    template_key: str = 'museum_white',
    ratio_key: str = '4:5',
    target_long_edge: int = 2048,
    render_params: Optional[RenderParams] = None,
    exif_data: Optional[Dict[str, Any]] = None,
    source_max_long_edge: int = 0,
) -> Optional[tuple[Image.Image, Dict[str, Any], ExifSource]]:
    """
    Process a single image: read EXIF, render with template.
    
    Returns (rendered_image, exif_dict, merged_exif) or None on error.
    """
    # Load image
    img = load_image(filepath, max_long_edge=source_max_long_edge)
    if img is None:
        return None
    
    # Read EXIF
    if exif_data is None:
        exif_data = read_exif(filepath)
    exif_src = ExifSource(**exif_data)
    
    # Determine ratio
    if ratio_key == 'Original' or ratio_key not in RATIOS or RATIOS[ratio_key] is None:
        # Use image's own aspect ratio
        from math import gcd
        g = gcd(img.width, img.height)
        ratio = (img.width // g, img.height // g)
    else:
        ratio = RATIOS[ratio_key]
    
    # Prepare render params
    if render_params is None:
        params = RenderParams()
    else:
        params = render_params
    
    params.ratio = ratio
    params.target_long_edge = target_long_edge
    
    # Select template
    template = TEMPLATES.get(template_key, TEMPLATES['museum_white'])
    
    # Render
    try:
        result_img = template.render(img, exif_src, params)
    except Exception as e:
        logger.error(f'Render error: {e}')
        return None
    
    merged = {
        'title': params.title or '',
        'location': params.location or exif_data['location'],
        'camera': params.camera or exif_data['camera'],
        'lens': params.lens or exif_data['lens'],
        'focal_length': params.focal_length or exif_data['focal_length'],
        'aperture': params.aperture or exif_data['aperture'],
        'shutter_speed': params.shutter_speed or exif_data['shutter_speed'],
        'iso': params.iso or exif_data['iso'],
        'date': params.date or exif_data['date'],
        'note': params.note or '',
        'has_gps': exif_data.get('has_gps', False),
        'gps_latitude': exif_data.get('gps_latitude'),
        'gps_longitude': exif_data.get('gps_longitude'),
        'map_url': exif_data.get('map_url', ''),
    }
    
    return result_img, merged, exif_src


def process_preview(
    filepath: str,
    template_key: str = 'museum_white',
    ratio_key: str = '4:5',
    render_params: Optional[RenderParams] = None,
    preview_long_edge: int = 800,
    exif_data: Optional[Dict[str, Any]] = None,
) -> Optional[Image.Image]:
    """
    Process an image for in-app preview (lower resolution).
    """
    if render_params is None:
        params = RenderParams()
    else:
        params = render_params
    
    # Keep layout stable across preview quality modes. Quality only changes the
    # final preview raster size; templates always compose at the same base size.
    preview_params = RenderParams(
        ratio=params.ratio,
        target_long_edge=PREVIEW_LAYOUT_LONG_EDGE,
        bg_color=params.bg_color,
        border_width=params.border_width,
        margin_top=params.margin_top,
        margin_side=params.margin_side,
        margin_bottom=params.margin_bottom,
        image_corner_radius=params.image_corner_radius,
        image_shadow=params.image_shadow,
        image_zoom=params.image_zoom,
        image_offset_x=params.image_offset_x,
        image_offset_y=params.image_offset_y,
        font_size=params.font_size,
        font_color=params.font_color,
        font_bold=params.font_bold,
        text_align=params.text_align,
        logo_enabled=params.logo_enabled,
        logo_size=params.logo_size,
        logo_position=params.logo_position,
        qr_enabled=params.qr_enabled,
        qr_size=params.qr_size,
        qr_position=params.qr_position,
        map_provider=params.map_provider,
        title=params.title,
        location=params.location,
        camera=params.camera,
        lens=params.lens,
        focal_length=params.focal_length,
        aperture=params.aperture,
        shutter_speed=params.shutter_speed,
        iso=params.iso,
        date=params.date,
        note=params.note,
        postcard_header=params.postcard_header,
        postcard_header_size=params.postcard_header_size,
        postcard_header_color=params.postcard_header_color,
        postcard_header_bold=params.postcard_header_bold,
        postmark_position=params.postmark_position,
    )
    
    result = process_image(
        filepath,
        template_key=template_key,
        ratio_key=ratio_key,
        target_long_edge=PREVIEW_LAYOUT_LONG_EDGE,
        render_params=preview_params,
        exif_data=exif_data,
        source_max_long_edge=max(PREVIEW_LAYOUT_LONG_EDGE, preview_long_edge),
    )
    
    if result:
        preview_img = result[0]
        current_long_edge = max(preview_img.size)
        if preview_long_edge > 0 and current_long_edge != preview_long_edge:
            scale = preview_long_edge / current_long_edge
            preview_img = preview_img.resize(
                (
                    max(1, int(preview_img.width * scale)),
                    max(1, int(preview_img.height * scale)),
                ),
                Image.LANCZOS,
            )
        return preview_img
    return None
