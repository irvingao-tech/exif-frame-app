"""Small disk cache for imported photo metadata and thumbnails."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

CACHE_VERSION = 1
APP_CACHE_NAME = 'EXIFFrameCard'


def cache_root() -> Path:
    """Return the per-user cache folder used by the app."""
    base = os.getenv('LOCALAPPDATA')
    if base:
        root = Path(base) / APP_CACHE_NAME / 'cache'
    else:
        root = Path.home() / f'.{APP_CACHE_NAME.lower()}' / 'cache'
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_stat(filepath: str):
    try:
        path = Path(filepath)
        stat = path.stat()
        return path, stat
    except OSError:
        return None, None


def cache_key(filepath: str, namespace: str, extra: str = '') -> str:
    """Build a key that changes when the source file changes."""
    path, stat = _safe_stat(filepath)
    if not path or not stat:
        raw = f'{CACHE_VERSION}|{namespace}|missing|{filepath}|{extra}'
    else:
        try:
            normalized = str(path.resolve()).lower()
        except OSError:
            normalized = str(path.absolute()).lower()
        raw = (
            f'{CACHE_VERSION}|{namespace}|{normalized}|'
            f'{stat.st_size}|{stat.st_mtime_ns}|{extra}'
        )
    return hashlib.sha1(raw.encode('utf-8', 'surrogatepass')).hexdigest()


def thumbnail_cache_path(filepath: str, size: int) -> Path:
    folder = cache_root() / 'thumbs'
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f'{cache_key(filepath, "thumb", str(size))}.png'


def _exif_cache_path(filepath: str) -> Path:
    folder = cache_root() / 'exif'
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f'{cache_key(filepath, "exif")}.json'


def get_cached_exif(filepath: str) -> dict[str, Any] | None:
    path = _exif_cache_path(filepath)
    if not path.exists():
        return None
    try:
        with path.open('r', encoding='utf-8') as f:
            payload = json.load(f)
        data = payload.get('data')
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def set_cached_exif(filepath: str, data: dict[str, Any]) -> None:
    path = _exif_cache_path(filepath)
    payload = {'version': CACHE_VERSION, 'data': data}
    try:
        with path.open('w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, separators=(',', ':'))
    except OSError:
        pass
