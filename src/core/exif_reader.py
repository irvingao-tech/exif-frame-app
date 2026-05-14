"""
EXIF Reader Module
Reads EXIF metadata from image files using Pillow + piexif.
Handles missing tags gracefully — returns empty strings for absent fields.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from PIL import Image
from PIL.ExifTags import Base as ExifBaseTags, GPSTAGS

logger = logging.getLogger(__name__)

# Common EXIF tag IDs from Pillow
EXIF_TAG_IDS = {
    'Make': 0x010F,
    'Model': 0x0110,
    'DateTimeOriginal': 0x9003,
    'DateTimeDigitized': 0x9004,
    'FocalLength': 0x920A,
    'FNumber': 0x829D,
    'ExposureTime': 0x829A,
    'ISOSpeedRatings': 0x8827,
    'LensModel': 0xA434,
    'LensMake': 0xA433,
    'ColorSpace': 0xA001,
    'ImageWidth': 0xA002,
    'ImageLength': 0xA003,
    'ExifImageWidth': 0xA002,
    'ExifImageHeight': 0xA003,
    'GPSInfo': 0x8825,
}

COLOR_SPACE_MAP = {
    1: 'sRGB',
    2: 'Adobe RGB',
    0xFFFF: 'Uncalibrated',
}


def _rational_to_float(rational) -> Optional[float]:
    """Convert IFDRational to float safely."""
    if rational is None:
        return None
    try:
        return float(rational)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _gps_to_decimal(values, ref: str) -> Optional[float]:
    """Convert GPS DMS (degrees, minutes, seconds) to decimal degrees."""
    if not values or len(values) < 3:
        return None
    try:
        degrees = _rational_to_float(values[0])
        minutes = _rational_to_float(values[1])
        seconds = _rational_to_float(values[2])
        if degrees is None or minutes is None or seconds is None:
            return None
        decimal = degrees + minutes / 60.0 + seconds / 3600.0
        if ref in ('S', 'W'):
            decimal = -decimal
        return round(decimal, 6)
    except Exception:
        return None


def _format_shutter_speed(exposure_time: float) -> str:
    """Format exposure time into human-readable shutter speed."""
    if exposure_time <= 0:
        return ''
    if exposure_time >= 1.0:
        return f'{exposure_time:.0f}s'
    # Fractional shutter speed
    denominator = round(1.0 / exposure_time)
    if abs(exposure_time - 1.0 / denominator) < 0.0001:
        return f'1/{denominator}s'
    return f'{exposure_time:.3f}s'


def read_exif(filepath: str) -> Dict[str, Any]:
    """
    Read EXIF data from an image file.
    
    Returns a dictionary with keys:
        camera, lens, focal_length, focal_length_35mm, aperture,
        shutter_speed, iso, date, location, color_space,
        image_width, image_height, has_gps
    
    All values are strings (formatted) or empty strings if missing.
    """
    result = {
        'camera': '',
        'lens': '',
        'focal_length': '',
        'focal_length_35mm': '',
        'aperture': '',
        'shutter_speed': '',
        'iso': '',
        'date': '',
        'location': '',
        'color_space': '',
        'image_width': 0,
        'image_height': 0,
        'has_gps': False,
        'gps_latitude': None,
        'gps_longitude': None,
        'map_url': '',
    }
    
    try:
        img = Image.open(filepath)
    except Exception as e:
        logger.warning(f'Cannot open image {filepath}: {e}')
        return result
    
    # Basic image dimensions
    result['image_width'] = img.width
    result['image_height'] = img.height
    
    # Try to get EXIF data
    try:
        exif_data = img._getexif()
    except Exception:
        exif_data = None
    
    if not exif_data:
        logger.info(f'No EXIF data found in {filepath}')
        return result
    
    # --- Camera Make & Model ---
    make = exif_data.get(EXIF_TAG_IDS['Make'], '')
    model = exif_data.get(EXIF_TAG_IDS['Model'], '')
    if isinstance(make, str) and isinstance(model, str):
        # Avoid duplicating make in model (e.g. "SONY" "SONY ILCE-7CM2")
        if model.startswith(make):
            result['camera'] = model.strip()
        else:
            result['camera'] = f'{make} {model}'.strip()
    elif model:
        result['camera'] = str(model).strip()
    elif make:
        result['camera'] = str(make).strip()
    
    # --- Lens ---
    lens_model = exif_data.get(EXIF_TAG_IDS['LensModel'], '')
    if lens_model:
        result['lens'] = str(lens_model).strip()
    
    # --- Focal Length ---
    fl = exif_data.get(EXIF_TAG_IDS['FocalLength'])
    if fl:
        fl_val = _rational_to_float(fl)
        if fl_val is not None:
            result['focal_length'] = f'{fl_val:.0f}mm'
    
    # Also try 35mm equivalent from piexif if available
    try:
        import piexif
        piexif_dict = piexif.load(filepath)
        exif_ifd = piexif_dict.get('Exif', {})
        fl_35 = exif_ifd.get(0xA405)  # FocalLengthIn35mmFilm
        if fl_35:
            result['focal_length_35mm'] = f'{fl_35}mm'
    except Exception:
        pass
    
    # --- Aperture (FNumber) ---
    fnumber = exif_data.get(EXIF_TAG_IDS['FNumber'])
    if fnumber:
        fn_val = _rational_to_float(fnumber)
        if fn_val is not None:
            result['aperture'] = f'f/{fn_val:.1f}'.rstrip('0').rstrip('.')
    
    # --- Shutter Speed ---
    exposure = exif_data.get(EXIF_TAG_IDS['ExposureTime'])
    if exposure:
        exp_val = _rational_to_float(exposure)
        if exp_val is not None:
            result['shutter_speed'] = _format_shutter_speed(exp_val)
    
    # --- ISO ---
    iso = exif_data.get(EXIF_TAG_IDS['ISOSpeedRatings'])
    if iso:
        try:
            if isinstance(iso, (list, tuple)):
                result['iso'] = f'ISO {iso[0]}'
            else:
                result['iso'] = f'ISO {iso}'
        except (TypeError, IndexError):
            pass
    
    # --- Date ---
    date_orig = exif_data.get(EXIF_TAG_IDS['DateTimeOriginal'])
    if not date_orig:
        date_orig = exif_data.get(EXIF_TAG_IDS['DateTimeDigitized'])
    if date_orig and isinstance(date_orig, str):
        try:
            dt = datetime.strptime(date_orig, '%Y:%m:%d %H:%M:%S')
            result['date'] = dt.strftime('%Y.%m.%d')
        except ValueError:
            result['date'] = date_orig
    
    # --- Color Space ---
    cs = exif_data.get(EXIF_TAG_IDS['ColorSpace'])
    if cs is not None:
        try:
            result['color_space'] = COLOR_SPACE_MAP.get(int(cs), f'ColorSpace({cs})')
        except (TypeError, ValueError):
            pass
    
    # --- GPS ---
    gps_data = exif_data.get(EXIF_TAG_IDS['GPSInfo'])
    if gps_data:
        try:
            lat_ref = gps_data.get(1, 'N')  # GPSLatitudeRef
            lat = gps_data.get(2)            # GPSLatitude
            lon_ref = gps_data.get(3, 'E')  # GPSLongitudeRef
            lon = gps_data.get(4)            # GPSLongitude
            
            lat_decimal = _gps_to_decimal(lat, lat_ref)
            lon_decimal = _gps_to_decimal(lon, lon_ref)
            
            if lat_decimal is not None and lon_decimal is not None:
                result['has_gps'] = True
                result['gps_latitude'] = lat_decimal
                result['gps_longitude'] = lon_decimal
                result['map_url'] = ''
                result['location'] = f'{lat_decimal:.4f}, {lon_decimal:.4f}'
        except Exception as e:
            logger.debug(f'GPS parse error: {e}')
    
    return result


def build_exif_text(exif: Dict[str, Any], location_override: str = '') -> str:
    """
    Build a single-line EXIF summary string from the extracted data.
    Smart format: only includes non-empty fields.
    """
    parts = []
    
    # Camera
    if exif.get('camera'):
        parts.append(exif['camera'])
    
    # Lens (only if different from camera)
    if exif.get('lens'):
        parts.append(exif['lens'])
    
    # Focal length
    if exif.get('focal_length'):
        parts.append(exif['focal_length'])
    
    # Aperture
    if exif.get('aperture'):
        parts.append(exif['aperture'])
    
    # Shutter speed
    if exif.get('shutter_speed'):
        parts.append(exif['shutter_speed'])
    
    # ISO
    if exif.get('iso'):
        parts.append(exif['iso'])
    
    # Location
    loc = location_override or exif.get('location', '')
    if loc:
        parts.append(loc)
    
    # Date
    if exif.get('date'):
        parts.append(exif['date'])
    
    return ' · '.join(parts)


# Convenience alias
read_exif_data = read_exif
