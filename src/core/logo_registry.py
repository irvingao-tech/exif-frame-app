"""
Brand logo detection and local asset lookup.

Logo image files are optional. Put PNG/JPG/WebP files under:
    src/assets/logos/

Use one of the registered brand keys as the filename, for example:
    canon.png, nikon.png, sony.png, fujifilm.png
"""

from pathlib import Path
from typing import Optional


LOGO_DIR = Path(__file__).resolve().parents[1] / 'assets' / 'logos'
LOGO_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp')


BRANDS = [
    {
        'key': 'canon',
        'label': 'Canon',
        'aliases': ['canon', 'eos', 'rf ', 'ef '],
    },
    {
        'key': 'nikon',
        'label': 'Nikon',
        'aliases': ['nikon', 'nikkor', ' z '],
    },
    {
        'key': 'sony',
        'label': 'Sony',
        'aliases': ['sony', 'ilce', 'alpha', 'sel', 'fe ', 'e-mount'],
    },
    {
        'key': 'apple',
        'label': 'Apple',
        'aliases': ['apple', 'iphone', 'ipad'],
    },
    {
        'key': 'fujifilm',
        'label': 'Fujifilm',
        'aliases': ['fujifilm', 'fuji', 'xf ', 'gf '],
    },
    {
        'key': 'leica',
        'label': 'Leica',
        'aliases': ['leica', 'summilux', 'summicron', 'noctilux'],
    },
    {
        'key': 'panasonic',
        'label': 'LUMIX',
        'aliases': ['panasonic', 'lumix'],
    },
    {
        'key': 'olympus',
        'label': 'OM System',
        'aliases': ['olympus', 'om system', 'm.zuiko', 'zuiko'],
    },
    {
        'key': 'ricoh',
        'label': 'Ricoh',
        'aliases': ['ricoh'],
    },
    {
        'key': 'pentax',
        'label': 'Pentax',
        'aliases': ['pentax'],
    },
    {
        'key': 'hasselblad',
        'label': 'Hasselblad',
        'aliases': ['hasselblad'],
    },
    {
        'key': 'sigma',
        'label': 'Sigma',
        'aliases': ['sigma'],
    },
    {
        'key': 'tamron',
        'label': 'Tamron',
        'aliases': ['tamron'],
    },
    {
        'key': 'zeiss',
        'label': 'Zeiss',
        'aliases': ['zeiss', 'carl zeiss', 'batis', 'loxia', 'otus'],
    },
    {
        'key': 'voigtlander',
        'label': 'Voigtlander',
        'aliases': ['voigtlander', 'voigtländer', 'nokton', 'apo-lanthar'],
    },
    {
        'key': 'laowa',
        'label': 'Laowa',
        'aliases': ['laowa', 'venus optics'],
    },
    {
        'key': 'viltrox',
        'label': 'Viltrox',
        'aliases': ['viltrox'],
    },
]


def detect_brand(camera: str = '', lens: str = '') -> Optional[dict]:
    """Detect the most likely brand from camera and lens strings."""
    camera_text = f' {camera or ""} '.lower()
    lens_text = f' {lens or ""} '.lower()

    for brand in BRANDS:
        if any(alias in camera_text for alias in brand['aliases']):
            return brand

    for brand in BRANDS:
        if any(alias in lens_text for alias in brand['aliases']):
            return brand

    return None


def find_logo_path(brand_key: str) -> Optional[Path]:
    """Return the first matching local logo image for a brand key."""
    for ext in LOGO_EXTENSIONS:
        candidate = LOGO_DIR / f'{brand_key}{ext}'
        if candidate.exists():
            return candidate
    return None
