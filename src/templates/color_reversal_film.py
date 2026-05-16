"""Color reversal film style border template."""

from PIL import Image, ImageDraw

from .base import (
    BaseTemplate, RenderParams, ExifSource,
    get_merged_exif, calculate_canvas,
    draw_shadow, load_font, template_colors, mix_color,
)


class ColorReversalFilmTemplate(BaseTemplate):
    name = 'Color Reversal Film'
    description = 'Dark reversal-film border with sprocket holes and EXIF markings'

    def render(self, image: Image.Image, exif: ExifSource, params: RenderParams) -> Image.Image:
        merged = get_merged_exif(exif, params)
        canvas_w, canvas_h, _scale = calculate_canvas(
            image.width, image.height, params.ratio, params.target_long_edge
        )

        bg_color, _font_color = template_colors(params, (245, 243, 238), (245, 180, 26))
        film_color = (54, 18, 34)
        film_shadow = (24, 8, 14)
        film_highlight = (88, 35, 52)
        mark_color = (255, 189, 28)
        hole_color = bg_color

        canvas = Image.new('RGB', (canvas_w, canvas_h), bg_color)
        draw = ImageDraw.Draw(canvas)

        outer_pad = max(10, int(min(canvas_w, canvas_h) * 0.018))
        film_box = (
            outer_pad,
            outer_pad,
            canvas_w - outer_pad,
            canvas_h - outer_pad,
        )
        draw.rounded_rectangle(
            film_box,
            radius=max(10, int(min(canvas_w, canvas_h) * 0.018)),
            fill=film_color,
        )

        band_h = max(58, int(canvas_h * 0.135))
        side_rail = max(28, int(canvas_w * 0.055))
        aperture_gap = max(12, int(min(canvas_w, canvas_h) * 0.022))

        aperture = (
            film_box[0] + side_rail,
            film_box[1] + band_h,
            film_box[2] - side_rail,
            film_box[3] - band_h,
        )
        aperture = (
            aperture[0] + aperture_gap,
            aperture[1] + aperture_gap // 2,
            aperture[2] - aperture_gap,
            aperture[3] - aperture_gap // 2,
        )
        radius = max(18, int(min(canvas_w, canvas_h) * 0.045))

        if params.image_shadow:
            canvas_rgba = canvas.convert('RGBA')
            canvas_rgba = draw_shadow(canvas_rgba, aperture, radius, alpha=45)
            canvas = canvas_rgba.convert('RGB')
            draw = ImageDraw.Draw(canvas)

        draw.rounded_rectangle(
            (
                aperture[0] - max(4, canvas_w // 320),
                aperture[1] - max(4, canvas_w // 320),
                aperture[2] + max(4, canvas_w // 320),
                aperture[3] + max(4, canvas_w // 320),
            ),
            radius=radius,
            fill=film_shadow,
        )

        img_area = (
            aperture[0],
            aperture[1],
            aperture[2],
            aperture[3],
        )
        area_w = max(1, img_area[2] - img_area[0])
        area_h = max(1, img_area[3] - img_area[1])
        user_zoom = max(100, min(220, int(params.image_zoom))) / 100
        img_scale = max(area_w / image.width, area_h / image.height) * user_zoom
        new_w = max(1, int(image.width * img_scale))
        new_h = max(1, int(image.height * img_scale))
        img_resized = image.resize((new_w, new_h), Image.LANCZOS)

        mask = Image.new('L', (area_w, area_h), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle((0, 0, area_w, area_h), radius=radius, fill=255)
        max_crop_x = max(0, new_w - area_w)
        max_crop_y = max(0, new_h - area_h)
        crop_x = max_crop_x // 2 + int((params.image_offset_x / 100) * (max_crop_x / 2))
        crop_y = max_crop_y // 2 + int((params.image_offset_y / 100) * (max_crop_y / 2))
        crop_x = max(0, min(crop_x, max_crop_x))
        crop_y = max(0, min(crop_y, max_crop_y))
        image_layer = img_resized.crop((crop_x, crop_y, crop_x + area_w, crop_y + area_h))
        canvas.paste(image_layer, (img_area[0], img_area[1]), mask)

        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle(
            img_area,
            radius=radius,
            outline=mix_color(film_color, (0, 0, 0), 0.45),
            width=max(2, canvas_w // 520),
        )

        self._draw_sprockets(draw, film_box, canvas_w, canvas_h, band_h, side_rail, hole_color, film_highlight)
        self._draw_film_markings(draw, film_box, canvas_w, canvas_h, band_h, merged, mark_color)
        return canvas

    def _draw_sprockets(
        self,
        draw: ImageDraw.ImageDraw,
        film_box,
        canvas_w: int,
        canvas_h: int,
        band_h: int,
        side_rail: int,
        hole_color,
        film_highlight,
    ):
        hole_w = max(18, int(canvas_w * 0.032))
        hole_h = max(28, int(canvas_h * 0.052))
        hole_radius = max(3, hole_w // 7)
        top_y = film_box[1] + max(22, band_h // 3)
        bottom_y = film_box[3] - max(22, band_h // 3) - hole_h
        start_x = film_box[0] + side_rail + max(4, canvas_w // 120)
        end_x = film_box[2] - side_rail - hole_w - max(4, canvas_w // 120)
        count = max(5, min(10, int((end_x - start_x) / max(1, hole_w * 2.1)) + 1))
        step = (end_x - start_x) / max(1, count - 1)

        for i in range(count):
            x = int(start_x + i * step)
            for y in (top_y, bottom_y):
                draw.rounded_rectangle(
                    (x, y, x + hole_w, y + hole_h),
                    radius=hole_radius,
                    fill=hole_color,
                    outline=film_highlight,
                    width=max(1, canvas_w // 1200),
                )

    def _draw_film_markings(self, draw, film_box, canvas_w: int, canvas_h: int, band_h: int, merged: dict, color):
        font_size = max(12, int(min(canvas_w, canvas_h) * 0.034))
        small_size = max(10, int(font_size * 0.88))
        font = load_font(font_size, True)
        small_font = load_font(small_size, True)

        lens = str(merged.get('lens') or '').strip()
        focal_length = str(merged.get('focal_length') or '').strip()
        iso = str(merged.get('iso') or '').replace('ISO ', '').strip()
        aperture = str(merged.get('aperture') or '').strip()
        top_left = lens
        if not top_left:
            fallback = [value for value in [focal_length, f'ISO {iso}' if iso else '', aperture] if value]
            top_left = '  /  '.join(fallback) or '35 mm COLOR'

        date = str(merged.get('date') or '').strip()
        camera = str(merged.get('camera') or 'COLOR FILM').strip()
        frame_no = (date.replace('.', '')[-2:] if date else '23') or '23'

        pad_x = max(12, int(canvas_w * 0.035))
        top_y = film_box[1] + max(6, band_h // 12)
        bottom_y = film_box[3] - max(8, band_h // 3)

        self._draw_fitted_text(draw, top_left, film_box[0] + pad_x, top_y,
                               max(1, canvas_w // 2), font_size, color, True, 'left', 8)
        self._draw_fitted_text(draw, frame_no, film_box[0], top_y,
                               canvas_w, font_size, color, True, 'center', 8)
        self._draw_fitted_text(draw, 'COLOR FILM', film_box[0], top_y,
                               film_box[2] - film_box[0] - pad_x, font_size,
                               color, True, 'right', 8)

        bottom_left = f'▶ {frame_no} A'
        bottom_mid = (focal_length or frame_no).replace('mm', ' mm').strip()
        bottom_right = camera
        self._draw_fitted_text(draw, bottom_left, film_box[0] + pad_x, bottom_y,
                               canvas_w // 3, small_size, color, True, 'left', 8)
        self._draw_fitted_text(draw, bottom_mid, film_box[0], bottom_y,
                               canvas_w, small_size, color, True, 'center', 8)
        self._draw_fitted_text(draw, bottom_right, film_box[0], bottom_y,
                               film_box[2] - film_box[0] - pad_x, small_size,
                               color, True, 'right', 8)
