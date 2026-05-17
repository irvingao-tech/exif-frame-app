"""Medium-format color reversal film border template."""

import random

from PIL import Image, ImageDraw, ImageFilter

from .base import (
    BaseTemplate, RenderParams, ExifSource,
    get_merged_exif, calculate_canvas,
    draw_shadow, load_font, template_colors,
)


class ColorReversalFilmTemplate(BaseTemplate):
    name = 'Color Reversal Film'
    description = 'Medium-format 120 reversal-film border with subtle EXIF markings'

    def render(self, image: Image.Image, exif: ExifSource, params: RenderParams) -> Image.Image:
        merged = get_merged_exif(exif, params)
        canvas_w, canvas_h, _scale = calculate_canvas(
            image.width, image.height, params.ratio, params.target_long_edge
        )

        bg_color, _font_color = template_colors(params, (246, 245, 242), (218, 166, 42))
        film_color = (17, 17, 16)
        film_edge = (64, 58, 50)
        mark_color = (255, 210, 56)

        canvas = Image.new('RGB', (canvas_w, canvas_h), bg_color)
        draw = ImageDraw.Draw(canvas)

        outer_pad = max(10, int(min(canvas_w, canvas_h) * 0.035))
        film_box = (
            outer_pad,
            outer_pad,
            canvas_w - outer_pad,
            canvas_h - outer_pad,
        )
        frame_radius = max(8, int(min(canvas_w, canvas_h) * 0.016))
        draw.rounded_rectangle(film_box, radius=frame_radius, fill=film_color)
        self._draw_film_texture(canvas, film_box, film_edge)
        draw = ImageDraw.Draw(canvas)

        band_h = max(48, int(canvas_h * 0.074))
        side_rail = max(32, int(canvas_w * 0.043))
        aperture_gap = max(5, int(min(canvas_w, canvas_h) * 0.006))
        aperture = (
            film_box[0] + side_rail + aperture_gap,
            film_box[1] + band_h + aperture_gap,
            film_box[2] - side_rail - aperture_gap,
            film_box[3] - band_h - aperture_gap,
        )
        radius = max(10, int(min(canvas_w, canvas_h) * 0.016))

        if params.image_shadow:
            canvas_rgba = canvas.convert('RGBA')
            canvas_rgba = draw_shadow(canvas_rgba, aperture, radius, alpha=28)
            canvas = canvas_rgba.convert('RGB')
            draw = ImageDraw.Draw(canvas)

        area_w = max(1, aperture[2] - aperture[0])
        area_h = max(1, aperture[3] - aperture[1])
        user_zoom = max(100, min(220, int(params.image_zoom))) / 100
        img_scale = max(area_w / image.width, area_h / image.height) * user_zoom
        new_w = max(1, int(image.width * img_scale))
        new_h = max(1, int(image.height * img_scale))
        img_resized = image.resize((new_w, new_h), Image.LANCZOS)

        max_crop_x = max(0, new_w - area_w)
        max_crop_y = max(0, new_h - area_h)
        crop_x = max_crop_x // 2 + int((params.image_offset_x / 100) * (max_crop_x / 2))
        crop_y = max_crop_y // 2 + int((params.image_offset_y / 100) * (max_crop_y / 2))
        crop_x = max(0, min(crop_x, max_crop_x))
        crop_y = max(0, min(crop_y, max_crop_y))
        image_layer = img_resized.crop((crop_x, crop_y, crop_x + area_w, crop_y + area_h))

        mask = Image.new('L', (area_w, area_h), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle((0, 0, area_w, area_h), radius=radius, fill=255)
        canvas.paste(image_layer, (aperture[0], aperture[1]), mask)

        draw = ImageDraw.Draw(canvas)
        self._draw_side_notches(draw, aperture, film_color, film_edge, canvas_w)
        self._draw_corner_wear(draw, film_box, canvas_w, canvas_h, film_edge)
        self._draw_film_markings(draw, film_box, canvas_w, canvas_h, band_h, merged, mark_color)
        return canvas

    def _draw_film_texture(self, canvas: Image.Image, film_box, edge_color):
        rng = random.Random(120)
        overlay = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        x1, y1, x2, y2 = film_box
        for _ in range(900):
            x = rng.randint(x1, max(x1, x2 - 1))
            y = rng.randint(y1, max(y1, y2 - 1))
            shade = rng.randint(24, 70)
            alpha = rng.randint(8, 18)
            od.point((x, y), fill=(shade, shade, shade, alpha))
        for _ in range(26):
            x = rng.randint(x1, x2)
            y = rng.randint(y1, y2)
            length = rng.randint(10, 42)
            alpha = rng.randint(16, 34)
            od.line(
                (x, y, min(x2, x + length), min(y2, y + rng.randint(-4, 5))),
                fill=(*edge_color, alpha),
                width=1,
            )
        overlay = overlay.filter(ImageFilter.GaussianBlur(0.25))
        composed = Image.alpha_composite(canvas.convert('RGBA'), overlay).convert('RGB')
        canvas.paste(composed)

    def _draw_side_notches(self, draw: ImageDraw.ImageDraw, aperture, film_color, edge_color, canvas_w: int):
        notch_r = max(4, canvas_w // 190)
        y = (aperture[1] + aperture[3]) // 2
        for x, start, end in (
            (aperture[0], 90, 270),
            (aperture[2], 270, 90),
        ):
            draw.pieslice(
                (x - notch_r, y - notch_r, x + notch_r, y + notch_r),
                start=start,
                end=end,
                fill=edge_color,
            )
            draw.pieslice(
                (x - notch_r // 2, y - notch_r // 2, x + notch_r // 2, y + notch_r // 2),
                start=start,
                end=end,
                fill=film_color,
            )

    def _draw_corner_wear(self, draw: ImageDraw.ImageDraw, film_box, canvas_w: int, canvas_h: int, edge_color):
        x1, y1, x2, y2 = film_box
        wear = max(10, min(canvas_w, canvas_h) // 70)
        width = max(1, min(canvas_w, canvas_h) // 520)
        marks = [
            (x1 + 6, y1 + wear, x1 + wear, y1 + 6),
            (x2 - wear, y1 + 6, x2 - 6, y1 + wear),
            (x1 + 6, y2 - wear, x1 + wear, y2 - 6),
            (x2 - wear, y2 - 6, x2 - 6, y2 - wear),
        ]
        for mark in marks:
            draw.line(mark, fill=edge_color, width=width)

    def _draw_film_markings(self, draw, film_box, canvas_w: int, canvas_h: int, band_h: int, merged: dict, color):
        font_size = max(12, int(min(canvas_w, canvas_h) * 0.026))
        small_size = max(10, int(font_size * 0.92))

        lens = str(merged.get('lens') or '').strip()
        focal_length = str(merged.get('focal_length') or '').strip()
        iso = str(merged.get('iso') or '').replace('ISO ', '').strip()
        aperture = str(merged.get('aperture') or '').strip()
        top_left = lens
        if not top_left:
            fallback = [value for value in [focal_length, f'ISO {iso}' if iso else '', aperture] if value]
            top_left = '  /  '.join(fallback) or '12'

        date = str(merged.get('date') or '').strip()
        camera = str(merged.get('camera') or 'COLOR FILM').strip()
        frame_no = (date.replace('.', '')[-2:] if date else '12') or '12'
        iso_label = f'ISO {iso}' if iso else 'ISO 400'

        pad_x = max(20, int(canvas_w * 0.07))
        top_y = film_box[1] + max(10, band_h // 5)
        bottom_y = film_box[3] - max(18, band_h // 2)

        self._draw_fitted_text(
            draw, top_left, film_box[0] + pad_x, top_y,
            max(1, int(canvas_w * 0.34)), font_size, color, False, 'left', 8,
        )
        self._draw_fitted_text(
            draw, '120', film_box[0], top_y,
            int(canvas_w * 0.82), font_size, color, False, 'center', 8,
        )
        self._draw_fitted_text(
            draw, iso_label, film_box[0], top_y,
            int(canvas_w * 1.08), font_size, color, False, 'center', 8,
        )
        self._draw_fitted_text(
            draw, '>', film_box[0], top_y,
            int(canvas_w * 1.38), font_size, color, False, 'center', 8,
        )
        self._draw_fitted_text(
            draw, frame_no, film_box[0], top_y,
            film_box[2] - film_box[0] - pad_x, font_size, color, False, 'right', 8,
        )

        bottom_left = f'< 400-{frame_no}'
        bottom_mid = (focal_length or frame_no).replace('mm', ' mm').strip()
        bottom_right = f'120  >  {camera}'
        self._draw_fitted_text(
            draw, bottom_left, film_box[0] + pad_x, bottom_y,
            canvas_w // 3, small_size, color, False, 'left', 8,
        )
        self._draw_fitted_text(
            draw, bottom_mid, film_box[0], bottom_y,
            canvas_w, small_size, color, False, 'center', 8,
        )
        self._draw_fitted_text(
            draw, bottom_right, film_box[0], bottom_y,
            film_box[2] - film_box[0] - pad_x, small_size, color, False, 'right', 8,
        )
