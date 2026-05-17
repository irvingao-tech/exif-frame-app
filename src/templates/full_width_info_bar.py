"""
Full Width Info Bar template.
Photo fills the full canvas width with a compact EXIF strip at the bottom.
"""

from PIL import Image, ImageDraw

from src.core.logo_registry import detect_brand, find_logo_path

from .base import (
    BaseTemplate, RenderParams, ExifSource,
    get_merged_exif, calculate_canvas,
    load_font, template_colors,
)


class FullWidthInfoBarTemplate(BaseTemplate):
    name = 'Full Width Info Bar'
    description = 'Full-width photo with a compact bottom EXIF information bar'

    def render(self, image: Image.Image, exif: ExifSource, params: RenderParams) -> Image.Image:
        merged = get_merged_exif(exif, params)
        canvas_w, canvas_h, _scale = calculate_canvas(
            image.width, image.height, params.ratio, params.target_long_edge
        )

        bg_color, font_color = template_colors(params, (255, 255, 255), (30, 30, 32))
        bar_h = max(112, int(canvas_h * 0.16))
        photo_h = max(1, canvas_h - bar_h)

        canvas = Image.new('RGB', (canvas_w, canvas_h), bg_color)
        photo = self._cover_image(image, canvas_w, photo_h, params.image_offset_y)
        canvas.paste(photo, (0, 0))

        draw = ImageDraw.Draw(canvas)
        draw.rectangle((0, photo_h, canvas_w, canvas_h), fill=bg_color)

        pad_x = max(18, int(canvas_w * 0.045))
        pad_y = max(12, int(bar_h * 0.22))
        main_size = max(13, int(bar_h * 0.20))
        detail_size = max(9, int(bar_h * 0.135))

        camera = str(merged.get('camera') or 'CAMERA').strip()
        lens = str(merged.get('lens') or '').strip()
        focal = str(merged.get('focal_length') or '').strip()
        aperture = str(merged.get('aperture') or '').strip()
        shutter = str(merged.get('shutter_speed') or '').strip()
        iso = str(merged.get('iso') or '').strip()
        date = str(merged.get('date') or '').strip()

        detail_parts = []
        if lens:
            detail_parts.append(lens)
        detail_parts.extend(part for part in [focal, aperture, shutter, iso, date] if part)
        detail_line = ' · '.join(detail_parts) or self._build_exif_line(merged) or camera

        bar_top = photo_h
        main_y = bar_top + pad_y
        detail_y = main_y + main_size + max(5, bar_h // 20)

        logo = self._load_brand_logo(merged, params, int(canvas_w * 0.28), int(bar_h * 0.48))
        logo_gap = max(16, canvas_w // 42)
        logo_box_w = logo['width'] if logo else 0
        logo_x = canvas_w - pad_x - logo_box_w
        text_w = max(1, (logo_x - logo_gap if logo else canvas_w - pad_x) - pad_x)

        self._draw_fitted_text(
            draw, camera, pad_x, main_y, text_w,
            main_size, font_color, True, 'left', 8,
        )
        self._draw_fitted_text(
            draw, detail_line, pad_x, detail_y, text_w,
            detail_size, (84, 84, 88), False, 'left', 6,
        )

        if logo:
            logo_y = bar_top + max(0, (bar_h - logo['height']) // 2)
            if logo.get('image'):
                canvas.paste(logo['image'], (logo_x, logo_y), logo['image'])
            else:
                draw.text((logo_x, logo_y), logo['text'], fill=font_color, font=logo['font'])

        return canvas

    def _cover_image(
        self,
        image: Image.Image,
        target_w: int,
        target_h: int,
        offset_y: int = 0,
    ) -> Image.Image:
        scale = max(target_w / image.width, target_h / image.height)
        new_w = max(1, int(image.width * scale))
        new_h = max(1, int(image.height * scale))
        resized = image.resize((new_w, new_h), Image.LANCZOS)
        crop_x = max(0, (new_w - target_w) // 2)
        max_crop_y = max(0, new_h - target_h)
        crop_y = max_crop_y // 2 + int((max(-100, min(100, offset_y)) / 100) * (max_crop_y / 2))
        crop_y = max(0, min(crop_y, max_crop_y))
        return resized.crop((crop_x, crop_y, crop_x + target_w, crop_y + target_h))

    def _load_brand_logo(
        self,
        merged: dict,
        params: RenderParams,
        max_width: int,
        max_height: int,
    ) -> dict | None:
        if not params.logo_enabled:
            return None

        brand = detect_brand(merged.get('camera', ''), merged.get('lens', ''))
        if not brand:
            return None

        logo_path = find_logo_path(brand['key'])
        if logo_path:
            try:
                logo_img = Image.open(logo_path).convert('RGBA')
                ratio = min(
                    max_height / max(logo_img.height, 1),
                    max_width / max(logo_img.width, 1),
                    1.0,
                )
                logo_img = logo_img.resize(
                    (
                        max(1, int(logo_img.width * ratio)),
                        max(1, int(logo_img.height * ratio)),
                    ),
                    Image.LANCZOS,
                )
                return {
                    'image': logo_img,
                    'width': logo_img.width,
                    'height': logo_img.height,
                }
            except Exception:
                pass

        draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
        label = brand.get('label', '').upper()
        fitted, font = self._fit_text(draw, label, max_width, max_height, True, 9)
        bbox = draw.textbbox((0, 0), fitted, font=font)
        return {
            'text': fitted,
            'font': font,
            'width': bbox[2] - bbox[0],
            'height': bbox[3] - bbox[1],
        }
