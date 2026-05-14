"""
Exporter module
Handles exporting the rendered image to JPG or PNG.
"""

import os
import logging
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)

EXPORT_RESOLUTIONS = {
    '1080px long edge': 1080,
    '2048px long edge': 2048,
    '3000px long edge': 3000,
    'Original high resolution': 0,  # 0 = use image's native dimensions
}


def export_image(
    image: Image.Image,
    output_path: str,
    format: str = 'JPEG',
    quality: int = 95,
    target_long_edge: int = 0,
) -> bool:
    """
    Export a rendered image to file.
    
    Args:
        image: PIL Image to export
        output_path: Full output file path
        format: 'JPEG' or 'PNG'
        quality: JPEG quality (1-100), ignored for PNG
        target_long_edge: Resize long edge before export (0 = no resize)
    
    Returns:
        True on success
    """
    try:
        img = image.copy()
        
        # Resize if needed
        if target_long_edge > 0:
            w, h = img.size
            if w >= h:
                if w > target_long_edge:
                    new_w = target_long_edge
                    new_h = int(h * target_long_edge / w)
                    img = img.resize((new_w, new_h), Image.LANCZOS)
            else:
                if h > target_long_edge:
                    new_h = target_long_edge
                    new_w = int(w * target_long_edge / h)
                    img = img.resize((new_w, new_h), Image.LANCZOS)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        
        # Save
        if format.upper() == 'PNG':
            img.save(output_path, 'PNG', optimize=True)
        else:
            img.save(output_path, 'JPEG', quality=quality, optimize=True, subsampling=0)
        
        logger.info(f'Exported: {output_path} ({img.size[0]}x{img.size[1]})')
        return True
    
    except Exception as e:
        logger.error(f'Export failed: {e}')
        return False


def generate_output_filename(input_path: str, suffix: str = '_framed', ext: str = '.jpg') -> str:
    """Generate output filename based on input filename."""
    base = os.path.splitext(os.path.basename(input_path))[0]
    return f'{base}{suffix}{ext}'


def batch_export(
    images: list,
    output_dir: str,
    format: str = 'JPEG',
    quality: int = 95,
    target_long_edge: int = 0,
    progress_callback=None,
) -> int:
    """
    Batch export multiple (filepath, rendered_image) pairs.
    
    Returns count of successful exports.
    """
    success_count = 0
    total = len(images)
    
    for i, (filepath, rendered_img) in enumerate(images):
        filename = generate_output_filename(filepath, '_framed', '.jpg' if format == 'JPEG' else '.png')
        output_path = os.path.join(output_dir, filename)
        
        if export_image(rendered_img, output_path, format, quality, target_long_edge):
            success_count += 1
        
        if progress_callback:
            progress_callback(i + 1, total)
    
    return success_count
